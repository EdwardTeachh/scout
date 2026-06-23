import sys
import types
import unittest


rich = types.ModuleType("rich")
console_mod = types.ModuleType("rich.console")
markup_mod = types.ModuleType("rich.markup")
panel_mod = types.ModuleType("rich.panel")
tree_mod = types.ModuleType("rich.tree")


class Console:
    def __init__(self, *args, **kwargs):
        pass

    def print(self, *args, **kwargs):
        pass


class Panel:
    @staticmethod
    def fit(*args, **kwargs):
        return args[0]


class Tree:
    def __init__(self, label):
        self.label = label
        self.children = []

    def add(self, label):
        child = Tree(label)
        self.children.append(child)
        return child


console_mod.Console = Console
markup_mod.escape = lambda value: value
panel_mod.Panel = Panel
tree_mod.Tree = Tree

sys.modules.setdefault("rich", rich)
sys.modules.setdefault("rich.console", console_mod)
sys.modules.setdefault("rich.markup", markup_mod)
sys.modules.setdefault("rich.panel", panel_mod)
sys.modules.setdefault("rich.tree", tree_mod)

import scout


class ScoutParserTests(unittest.TestCase):
    def test_parse_status(self):
        active = "Loaded: loaded\n     Active: active (running)\n"
        inactive = "Loaded: loaded\n     Active: failed (Result: exit-code)\n"
        missing = "Unit demo.service could not be found."

        self.assertEqual(scout.parse_status(active, 0), "active")
        self.assertEqual(scout.parse_status(inactive, 3), "inactive")
        self.assertEqual(scout.parse_status(missing, 4), "not_found")

    def test_parse_unit_file(self):
        output = "# /etc/systemd/system/demo.service\n[Service]\nExecStart=/usr/bin/demo\n"
        self.assertEqual(scout.parse_unit_file(output), "/etc/systemd/system/demo.service")

    def test_parse_autostart(self):
        enabled = scout.CommandResult("enabled\n", "", 0)
        failed = scout.CommandResult("", "Failed to get unit file state\n", 1)
        timed_out = scout.CommandResult("", "", 1, timed_out=True)

        self.assertEqual(scout.parse_autostart(enabled), "enabled")
        self.assertEqual(scout.parse_autostart(failed), "error")
        self.assertEqual(scout.parse_autostart(timed_out), "timeout")

    def test_unit_values_allow_indentation(self):
        output = "[Service]\n  ExecStart=/usr/bin/demo --config /etc/demo/demo.yaml\n"
        self.assertEqual(
            scout.unit_values(output, "ExecStart"),
            ["/usr/bin/demo --config /etc/demo/demo.yaml"],
        )

    def test_environment_file_paths(self):
        values = ["-/etc/default/demo /etc/demo/env"]
        self.assertEqual(
            scout.environment_file_paths(values),
            ["/etc/default/demo", "/etc/demo/env"],
        )

    def test_exec_config_paths(self):
        values = [
            "/usr/bin/demo --config /etc/demo/demo.yaml -c /etc/demo/extra.conf /etc/demo/state.db"
        ]
        self.assertEqual(
            scout.exec_config_paths(values),
            ["/etc/demo/demo.yaml", "/etc/demo/extra.conf", "/etc/demo/state.db"],
        )

    def test_environment_log_paths(self):
        values = ["LOG_FILE=/var/log/demo.log OTHER=value"]
        self.assertEqual(scout.environment_log_paths(values), ["/var/log/demo.log"])


if __name__ == "__main__":
    unittest.main()
