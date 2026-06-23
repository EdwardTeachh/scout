# Scout

## English

### 1. Installation

```sh
curl -fsSL https://raw.githubusercontent.com/EdwardTeachh/scout/main/install.sh | bash
```

The installer:

- checks Linux, systemd, systemctl, python3, curl, and rich
- does not install dependencies
- downloads `scout.py` from GitHub
- installs it to `/usr/local/bin/scout`
- uses sudo only when required
- creates `~/.config/scout/config` if missing

### 2. Requirements

- Linux
- systemd
- systemctl
- Python 3
- curl
- rich Python library

### 3. Usage

```sh
scout <service>
```

### 4. Example output

```text
$ scout ssh
ssh
├── Status: Active
├── Unit file: /usr/lib/systemd/system/ssh.service (exists)
├── ExecStart
│   └── /usr/sbin/sshd -D $SSHD_OPTS
├── Configuration paths
│   └── /etc/default/ssh (exists)
└── Logs
    └── Suggested journal command: journalctl -u ssh -n 50 --no-pager
```

### 5. What is Scout

Scout is a read-only Linux CLI utility for inspecting the topology of a systemd service.

### 6. What Scout does

- is written in Python
- uses `rich` to render tree-style output
- reads only `systemctl status <service>` and `systemctl cat <service>`
- shows service status
- shows unit file path
- shows `ExecStart` command(s)
- shows explicitly referenced configuration paths
- shows explicitly referenced log paths or a `journalctl` command
- checks file paths: green if exists, red if missing, lock icon if permission is denied

### 7. What Scout does NOT do

- does not scan the filesystem
- does not guess or infer paths
- does not expand environment variables
- does not parse included configuration files
- does not inspect runtime-generated files
- does not read logs itself
- does not modify system state

### 8. Configuration

User configuration file:

```text
~/.config/scout/config
```

Language setting:

```text
LANG=en
LANG=ru
```

### 9. Design philosophy

- predictable behavior
- read-only inspection
- explicit data sources
- safe to run on production systems
- no hidden logic or heuristics

---

## Русский

### 1. Установка

```sh
curl -fsSL https://raw.githubusercontent.com/EdwardTeachh/scout/main/install.sh | bash
```

Установщик:

- проверяет Linux, systemd, systemctl, python3, curl и rich
- не устанавливает зависимости
- скачивает `scout.py` с GitHub
- устанавливает его в `/usr/local/bin/scout`
- использует sudo только когда требуется
- создаёт `~/.config/scout/config`, если файла нет

### 2. Требования

- Linux
- systemd
- systemctl
- Python 3
- curl
- Python-библиотека rich

### 3. Использование

```sh
scout <service>
```

### 4. Пример вывода

```text
$ scout ssh
ssh
├── Статус: Активен
├── Файл unit: /usr/lib/systemd/system/ssh.service (существует)
├── ExecStart
│   └── /usr/sbin/sshd -D $SSHD_OPTS
├── Пути конфигурации
│   └── /etc/default/ssh (существует)
└── Логи
    └── Команда journal: journalctl -u ssh -n 50 --no-pager
```

### 5. Что такое Scout

Scout — это read-only Linux CLI-утилита для просмотра топологии systemd-сервиса.

### 6. Что делает Scout

- написан на Python
- использует `rich` для вывода в виде дерева
- читает только `systemctl status <service>` и `systemctl cat <service>`
- показывает статус сервиса
- показывает путь к unit-файлу
- показывает команду или команды `ExecStart`
- показывает явно указанные пути конфигурации
- показывает явно указанные пути логов или команду `journalctl`
- проверяет пути файлов: зелёный если существует, красный если отсутствует, значок замка если доступ запрещён

### 7. Что Scout НЕ делает

- не сканирует файловую систему
- не угадывает и не выводит пути по предположению
- не раскрывает переменные окружения
- не разбирает подключённые конфигурационные файлы
- не проверяет файлы, созданные во время работы сервиса
- не читает логи сам
- не изменяет состояние системы

### 8. Конфигурация

Пользовательский файл конфигурации:

```text
~/.config/scout/config
```

Настройка языка:

```text
LANG=en
LANG=ru
```

### 9. Философия дизайна

- предсказуемое поведение
- read-only просмотр
- явные источники данных
- безопасно запускать на production-системах
- без скрытой логики и эвристик
