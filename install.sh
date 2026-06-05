#!/usr/bin/env bash
set -u

error() {
  printf 'Error: %s\n' "$1" >&2
}

info() {
  printf '%s\n' "$1"
}

if [ "$(uname -s)" != "Linux" ]; then
  error "Scout can only be installed on Linux."
  exit 1
fi

if ! command -v systemctl >/dev/null 2>&1; then
  error "systemctl is required but was not found."
  exit 1
fi

if [ ! -r /proc/1/comm ]; then
  error "Cannot verify that PID 1 is systemd."
  exit 1
fi

if [ "$(cat /proc/1/comm)" != "systemd" ]; then
  error "systemd must be the init system."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  error "python3 is required but was not found."
  exit 1
fi

if ! python3 -c "import rich" >/dev/null 2>&1; then
  error "Python module 'rich' is missing."
  info "Install it manually, then run this installer again."
  info "Examples:"
  info "  python3 -m pip install rich"
  info "  sudo apt install python3-rich"
  info "  sudo dnf install python3-rich"
  info "  sudo pacman -S python-rich"
  exit 1
fi

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SOURCE_FILE="$SCRIPT_DIR/scout.py"
TARGET_FILE="/usr/local/bin/scout"
CONFIG_DIR="$HOME/.config/scout"
CONFIG_FILE="$CONFIG_DIR/config"

if [ ! -f "$SOURCE_FILE" ]; then
  error "scout.py was not found next to install.sh."
  exit 1
fi

if ! cp "$SOURCE_FILE" "$TARGET_FILE" 2>/dev/null; then
  error "Cannot write to /usr/local/bin/scout."
  info "Try running this installer with sudo."
  exit 1
fi

if ! chmod +x "$TARGET_FILE" 2>/dev/null; then
  error "Cannot make /usr/local/bin/scout executable."
  info "Try running this installer with sudo."
  exit 1
fi

if [ -f "$CONFIG_FILE" ]; then
  info "Existing config kept: $CONFIG_FILE"
else
  if [ ! -r /dev/tty ] || [ ! -w /dev/tty ]; then
    error "Interactive terminal /dev/tty is required to create config."
    exit 1
  fi

  if ! mkdir -p "$CONFIG_DIR"; then
    error "Cannot create config directory: $CONFIG_DIR"
    exit 1
  fi

  printf 'Choose Scout language:\n' >/dev/tty
  printf '1) English\n' >/dev/tty
  printf '2) Русский\n' >/dev/tty
  printf '> ' >/dev/tty

  IFS= read -r language_choice </dev/tty

  case "$language_choice" in
    1)
      scout_lang="en"
      ;;
    2)
      scout_lang="ru"
      ;;
    *)
      error "Invalid language choice."
      exit 1
      ;;
  esac

  if ! printf 'LANG=%s\n' "$scout_lang" >"$CONFIG_FILE"; then
    error "Cannot write config file: $CONFIG_FILE"
    exit 1
  fi

  info "Config created: $CONFIG_FILE"
fi

info "Scout installed: $TARGET_FILE"
