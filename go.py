#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import sys
import traceback

from core import (
    GoException,
    ParameterAvailabilityException,
    AvailabilityEnum,
    is_like_a_version,
)

import settings

# NOTE: Нужно для работы core.commands
settings.run_settings_preprocess()
SETTINGS = settings.SETTINGS

from core.commands import (
    Command,
    resolve_actions,
    resolve_version,
)
from settings import get_project, resolve_name


ABOUT_TEXT = r"""
RUN:
  go <name> <version> <action> - Run tool
  go <name> <action>           - Run tool (trunk version)
  go <name> open <version>     - Open dir version
  go <name> open               - Open dir
  go <name>                    - Print versions
  go -d                        - Print settings

SUPPORTED NAMES:
  {}

EXAMPLES:
  > go optt trunk designer
    Run: "C:/DEV__OPTT/trunk_optt/!!designer.cmd"

  > go tx 3.2.6.10 server
    Run: "C:/DEV__TX/3.2.6.10/!!server.cmd"

  > go tx 6 server
    Run: "C:/DEV__TX/3.2.6.10/!!server.cmd"

  > go tx 3.2.6,3.2.7,trunk server
    Run: "C:/DEV__TX/3.2.6.10/!!server.cmd"

  > go tx 3.2.6-trunk server
    Run: "C:/DEV__TX/3.2.6.10/!!server.cmd"

  > $ go tx 35 u
    Run: svn update in C:\DEV__TX\3.2.35.10

  > $ go tx 35 u -f
    Run: svn update in C:\DEV__TX\3.2.35.10

  > go tx designer
    Run: "C:/DEV__TX/trunk_tx/!!designer.cmd"

  > go tx get_last
    Run: tx call 'get_last_release_version'
    Последняя версия релиза для trunk: 3.2.36.10
    
  > go tx 34 get_last
    Run: tx call 'get_last_release_version'
    Последняя версия релиза для 3.2.34.10: 3.2.34.10.17

  > go tx find_ver TXI-8197
    Run: tx call 'find_versions' (['TXI-8197'])
    Строка 'TXI-8197' встречается в версиях: trunk, 3.2.36.10, 3.2.35.10, 3.2.34.10
    
  > go tx 34-35 find_rele TXI-8197
    Run: tx call 'find_release_versions' (['TXI-8197'])
    Коммит с 'TXI-8197' в 3.2.34.10 попал в версию: 3.2.34.10.18
    
    Run: tx call 'find_release_versions' (['TXI-8197'])
    Коммит с 'TXI-8197' в 3.2.35.10 попал в версию: 3.2.35.10.11

  > go open optt trunk
    Open: "C:/DEV__OPTT/trunk_optt"

  > go open optt
    Open: "C:/DEV__OPTT"

  > go optt
    Supported versions: 2.1.10, trunk_optt
    Supported actions: build, cleanup, compile, designer, explorer, log, server, update
    
  > go optt kill
  > go optt kill -d
  > go optt kill -s
  > go optt kill -e
  > go optt kill -a
  > go optt kill -se
  
  > go tx s pg
    Запуск: 'C:\\DEV__TX\\trunk\\!!server-postgres.cmd'
    
  > go tx s+e pg
    Запуск: 'C:\\DEV__TX\\trunk\\!!server-postgres.cmd'
    Запуск: 'C:\\DEV__TX\\trunk\\!!explorer.cmd'
""".format(
    ", ".join(SETTINGS.keys()),
).strip()


def parse_cmd_args(args: list[str]) -> list[Command]:
    args: list[str] = args.copy()
    name: str | None = None

    actions: list[str | None] = []
    versions: list[str | None] = []

    # Первый аргумент <name>
    if args:
        alias: str = args.pop(0).lower()
        name = resolve_name(alias)

    options: dict = get_project(name)["options"]
    maybe_version: bool = options["version"] != AvailabilityEnum.PROHIBITED
    maybe_action: bool = options["action"] != AvailabilityEnum.PROHIBITED

    # Второй аргумент это или <version>, или <action>
    if (maybe_version or maybe_action) and args:
        alias: str = args.pop(0).lower()

        if (
            is_like_a_version(alias)
            and options["version"] != AvailabilityEnum.PROHIBITED
        ):
            # Например, "3.2.23,3.2.24,3.2.25,trunk"
            if "," in alias:
                for x in alias.split(","):
                    version = resolve_version(name, x)
                    versions.append(version)

            elif "-" in alias:  # Например, "3.2.23-trunk"
                start, end = alias.split("-")
                start = resolve_version(name, start)
                end = resolve_version(name, end)

                found = False
                for version in get_project(name)["versions"]:
                    if start == version:
                        found = True

                    if not found:
                        continue

                    versions.append(version)

                    if end in version:
                        break

            else:
                version = resolve_version(name, alias)
                versions.append(version)

        elif options["action"] != AvailabilityEnum.PROHIBITED:
            actions += resolve_actions(name, alias)

    # Третий аргумент <action>
    if maybe_action and args and not actions:
        alias: str = args.pop(0).lower()
        actions += resolve_actions(name, alias)

    if not versions:
        versions.append(None)

    if not actions:
        actions.append(None)

    commands = []
    for version in versions:
        for action in actions:
            commands.append(Command(name, version, action, args))
    return commands


def run(args: list[str]):
    try:
        for command in parse_cmd_args(args):
            command.run()

    except ParameterAvailabilityException as e:
        name: str = e.command.name
        settings: dict = get_project(name)
        options: dict = settings["options"]

        is_answered: bool = False

        # Если для сущности параметр версии возможен
        if options["version"] != AvailabilityEnum.PROHIBITED:
            supported_versions = ", ".join(sorted(settings["versions"]))
            print(f"Поддерживаемые версии: {supported_versions}")
            is_answered = True

        # Если для сущности параметр action возможен
        if options["action"] != AvailabilityEnum.PROHIBITED:
            supported_actions = ", ".join(sorted(settings["actions"]))
            print(f"Поддерживаемые действия: {supported_actions}")
            is_answered = True

        if not is_answered:
            print(e)

    except GoException as e:
        # Если передан флаг отладки
        show_exception_flag = "-e"
        if args[-1].lower().startswith(show_exception_flag):
            print(traceback.format_exc())
        else:
            print(e)
            print(
                f"Чтобы увидеть ошибку с стеком нужно "
                f"повторить команду с флагом {show_exception_flag}"
            )


def _print_help():
    print(ABOUT_TEXT)
    sys.exit()


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "-h":
        _print_help()

    if args and args[0] == "-d":
        import json
        from settings import PATH_SETTINGS

        print(PATH_SETTINGS)
        print(json.dumps(SETTINGS, indent=4, default=repr))
        sys.exit()

    run(args)
