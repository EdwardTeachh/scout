#!/usr/bin/env python3
import argparse
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.tree import Tree


CONFIG_PATH = os.path.expanduser("~/.config/scout/config")
CONFIG_EXTENSIONS = (".conf", ".json", ".yaml", ".yml", ".db")
LOG_EXTENSIONS = (".log",)
SYSTEMCTL_TIMEOUT_SECONDS = 10
VERSION = "1.1"


TRANSLATIONS = {
    "en": {
        "title": "Scout",
        "status": "Status",
        "autostart": "Autostart",
        "active": "Active",
        "inactive": "Inactive",
        "not_found": "Not Found",
        "unknown": "Unknown",
        "unit_file": "Unit file",
        "exec_start": "ExecStart",
        "configuration": "Configuration paths",
        "logs": "Logs",
        "journal": "Suggested journal command",
        "exists": "exists",
        "missing": "missing",
        "inaccessible": "inaccessible",
        "none": "None",
        "systemctl_missing": "systemctl is not available",
        "systemctl_timeout": "systemctl timed out",
        "error": "error",
        "timeout": "timeout",
        "enabled": "enabled",
        "disabled": "disabled",
        "static": "static",
        "masked": "masked",
        "indirect": "indirect",
        "generated": "generated",
    },
    "ru": {
        "title": "Scout",
        "status": "Статус",
        "autostart": "Автозагрузка",
        "active": "Активен",
        "inactive": "Неактивен",
        "not_found": "Не найден",
        "unknown": "Неизвестно",
        "unit_file": "Файл unit",
        "exec_start": "ExecStart",
        "configuration": "Пути конфигурации",
        "logs": "Логи",
        "journal": "Команда journal",
        "exists": "существует",
        "missing": "отсутствует",
        "inaccessible": "нет доступа",
        "none": "Нет",
        "systemctl_missing": "systemctl недоступен",
        "systemctl_timeout": "systemctl не ответил вовремя",
        "error": "ошибка",
        "timeout": "таймаут",
        "enabled": "включена",
        "disabled": "выключена",
        "static": "static",
        "masked": "masked",
        "indirect": "indirect",
        "generated": "generated",
    },
}


@dataclass(frozen=True)
class PathState:
    path: str
    exists: bool
    inaccessible: bool


@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool = False


def load_language() -> str:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
            for line in config_file:
                if line.strip() == "LANG=ru":
                    return "ru"
    except OSError:
        pass
    return "en"


def run_command(command: list[str]) -> CommandResult | None:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=SYSTEMCTL_TIMEOUT_SECONDS,
        )
        return CommandResult(result.stdout, result.stderr, result.returncode)
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired as error:
        return CommandResult(error.stdout or "", error.stderr or "", 1, timed_out=True)


def parse_status(status_output: str, return_code: int) -> str:
    if return_code == 4 or "could not be found" in status_output.lower():
        return "not_found"

    match = re.search(r"^\s*Active:\s+(\w+)", status_output, re.MULTILINE)
    if not match:
        return "unknown"

    state = match.group(1).lower()
    if state == "active":
        return "active"
    if state in {"inactive", "failed", "deactivating", "activating", "reloading"}:
        return "inactive"
    return "unknown"


def parse_autostart(result: CommandResult) -> str:
    if result.timed_out:
        return "timeout"

    value = result.stdout.strip().splitlines()
    if result.returncode == 0 and value:
        return value[0].strip()

    error_value = result.stderr.strip().splitlines()
    if error_value:
        return "error"
    return "error"


def parse_unit_file(cat_output: str) -> str | None:
    for line in cat_output.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            path = stripped[2:].strip()
            return path or None
        if stripped:
            return None
    return None


def logical_unit_lines(cat_output: str) -> list[str]:
    lines: list[str] = []
    current = ""

    for raw_line in cat_output.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            if current:
                lines.append(current)
                current = ""
            continue

        if line.endswith("\\"):
            current += line[:-1].strip() + " "
            continue

        current += line.strip()
        lines.append(current)
        current = ""

    if current:
        lines.append(current)

    return lines


def unit_values(cat_output: str, key: str) -> list[str]:
    prefix = f"{key}="
    values: list[str] = []
    for line in logical_unit_lines(cat_output):
        stripped = line.lstrip()
        if stripped.startswith(prefix):
            value = stripped[len(prefix) :].strip()
            if value:
                values.append(value)
    return values


def strip_systemd_prefix(value: str) -> str:
    return value.lstrip("-+!@:")


def split_command(value: str) -> list[str]:
    try:
        return shlex.split(strip_systemd_prefix(value), posix=True)
    except ValueError:
        return strip_systemd_prefix(value).split()


def environment_file_paths(values: Iterable[str]) -> list[str]:
    paths: list[str] = []
    for value in values:
        for token in split_command(value):
            path = token[1:] if token.startswith("-/") else token
            if path.startswith("/"):
                paths.append(path)
    return paths


def looks_like_config_path(path: str) -> bool:
    return path.lower().endswith(CONFIG_EXTENSIONS)


def looks_like_log_path(path: str) -> bool:
    return path.lower().endswith(LOG_EXTENSIONS)


def exec_config_paths(exec_values: Iterable[str]) -> list[str]:
    paths: list[str] = []
    config_flags = {"-c", "--config"}

    for value in exec_values:
        tokens = split_command(value)
        skip_next = False
        for index, token in enumerate(tokens):
            if skip_next:
                skip_next = False
                continue

            if token in config_flags and index + 1 < len(tokens):
                next_token = tokens[index + 1]
                if next_token.startswith("/"):
                    paths.append(next_token)
                    skip_next = True
                continue

            if token.startswith("--config="):
                path = token.split("=", 1)[1]
                if path.startswith("/"):
                    paths.append(path)
                continue

            if token.startswith("/") and looks_like_config_path(token):
                paths.append(token)

    return paths


def environment_log_paths(environment_values: Iterable[str]) -> list[str]:
    paths: list[str] = []
    for value in environment_values:
        for token in split_command(value):
            assignment_value = token.split("=", 1)[1] if "=" in token else token
            if assignment_value.startswith("/") and looks_like_log_path(assignment_value):
                paths.append(assignment_value)
    return paths


def unique_paths(paths: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            result.append(path)
    return result


def validate_path(path: str) -> PathState:
    try:
        os.stat(path)
        exists = True
    except FileNotFoundError:
        return PathState(path=path, exists=False, inaccessible=False)
    except PermissionError:
        return PathState(path=path, exists=True, inaccessible=True)
    except OSError:
        exists = os.path.exists(path)
        if not exists:
            return PathState(path=path, exists=False, inaccessible=False)
        return PathState(path=path, exists=True, inaccessible=True)

    inaccessible = False
    if exists:
        try:
            if os.path.isdir(path):
                os.listdir(path)
            else:
                with open(path, "rb"):
                    pass
        except PermissionError:
            inaccessible = True
        except OSError:
            inaccessible = True

    return PathState(path=path, exists=exists, inaccessible=inaccessible)


def path_label(state: PathState, text: dict[str, str]) -> str:
    path = escape(state.path)
    if state.exists and state.inaccessible:
        return f"[green]{path}[/green] 🔒 [yellow]({text['inaccessible']})[/yellow]"
    if state.exists:
        return f"[green]{path}[/green] [green]({text['exists']})[/green]"
    if state.inaccessible:
        return f"[red]{path}[/red] 🔒 [yellow]({text['inaccessible']})[/yellow]"
    return f"[red]{path}[/red] [red]({text['missing']})[/red]"


def autostart_label(value: str, text: dict[str, str]) -> str:
    colors = {
        "enabled": "green",
        "disabled": "yellow",
        "masked": "red",
        "static": "dim",
        "error": "red",
        "timeout": "red",
    }
    translated = text.get(value, value)
    if translated != value:
        label = f"{translated} ({value})"
    else:
        label = translated
    color = colors.get(value)
    escaped_label = escape(label)
    if color:
        return f"[{color}]{escaped_label}[/{color}]"
    return escaped_label


def build_tree(
    service: str,
    status_key: str,
    autostart_value: str,
    cat_output: str,
    text: dict[str, str],
) -> Tree:
    escaped_service = escape(service)
    tree = Tree(f"[bold]{escaped_service}[/bold]")
    tree.add(f"{text['status']}: [bold]{text[status_key]}[/bold]")
    tree.add(f"{text['autostart']}: {autostart_label(autostart_value, text)}")

    unit_file = parse_unit_file(cat_output)
    if unit_file:
        tree.add(f"{text['unit_file']}: {path_label(validate_path(unit_file), text)}")

    exec_values = unit_values(cat_output, "ExecStart")
    if exec_values:
        exec_branch = tree.add(text["exec_start"])
        for value in exec_values:
            exec_branch.add(escape(value))

    environment_files = environment_file_paths(unit_values(cat_output, "EnvironmentFile"))
    config_paths = unique_paths(environment_files + exec_config_paths(exec_values))
    if config_paths:
        config_branch = tree.add(text["configuration"])
        for path in config_paths:
            config_branch.add(path_label(validate_path(path), text))

    log_paths = unique_paths(environment_log_paths(unit_values(cat_output, "Environment")))
    log_states = [validate_path(path) for path in log_paths]
    existing_log_paths = [state for state in log_states if state.exists]
    logs_branch = tree.add(text["logs"])
    if existing_log_paths:
        for state in existing_log_paths:
            logs_branch.add(path_label(state, text))
    else:
        journal_service = escape(shlex.quote(service))
        logs_branch.add(f"{text['journal']}: journalctl -u {journal_service} -n 50 --no-pager")

    return tree


def render_error(service: str, message: str, text: dict[str, str], no_color: bool = False) -> None:
    console = Console(no_color=no_color)
    console.print(Panel.fit(escape(service), title=text["title"]))
    tree = Tree(f"[bold]{escape(service)}[/bold]")
    tree.add(f"[red]{message}[/red]")
    console.print(tree)


def main() -> int:
    parser = argparse.ArgumentParser(prog="scout")
    parser.add_argument("--version", action="version", version=f"Scout {VERSION}")
    parser.add_argument("--no-color", action="store_true", help="disable colored output")
    parser.add_argument("service")
    args = parser.parse_args()

    language = load_language()
    text = TRANSLATIONS[language]
    no_color = args.no_color or "NO_COLOR" in os.environ
    console = Console(no_color=no_color)

    status_result = run_command(["systemctl", "status", args.service])
    cat_result = run_command(["systemctl", "cat", args.service])
    is_enabled_result = run_command(["systemctl", "is-enabled", args.service])

    if status_result is None or cat_result is None or is_enabled_result is None:
        render_error(args.service, text["systemctl_missing"], text, no_color=no_color)
        return 1

    if status_result.timed_out or cat_result.timed_out:
        render_error(args.service, text["systemctl_timeout"], text, no_color=no_color)
        return 1

    status_output = status_result.stdout + status_result.stderr
    status_key = parse_status(status_output, status_result.returncode)
    autostart_value = parse_autostart(is_enabled_result)
    cat_output = cat_result.stdout if cat_result.returncode == 0 else ""

    console.print(Panel.fit(escape(args.service), title=text["title"]))
    console.print(build_tree(args.service, status_key, autostart_value, cat_output, text))
    return 0 if status_key != "not_found" else 1


if __name__ == "__main__":
    sys.exit(main())
