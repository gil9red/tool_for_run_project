#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import sys
import traceback

from core import (
    GoException,
    ParameterAvailabilityException,
    AvailabilityEnum,
    get_similar_value,
    is_like_a_version,
)

import settings

# NOTE: Нужно для работы core.commands
settings.run_settings_preprocess()
SETTINGS = settings.SETTINGS

from core.commands import (
    Command,
    resolve_whats,
    resolve_version,
)
from settings import get_settings, resolve_name


def has_similar_value(alias: str, items: list) -> bool:
    return get_similar_value(alias, items) is not None


ABOUT_TEXT = r"""
RUN:
  go <name> <version> <what> - Run tool
  go <name> <what>           - Run tool (trunk version)
  go <name> open <version>   - Open dir version
  go <name> open             - Open dir
  go <name>                  - Print versions
  go -d                      - Print settings

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
    Supported <what>: build, cleanup, compile, designer, explorer, log, server, update
    
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
    args = args.copy()
    name, whats = [None] * 2
    versions = []

    # Первый аргумент <name>
    if args:
        name = args.pop(0).lower()
        name = resolve_name(name)

    options = get_settings(name)["options"]
    maybe_version = options["version"] != AvailabilityEnum.PROHIBITED
    maybe_what = options["what"] != AvailabilityEnum.PROHIBITED

    # Второй аргумент это или <version>, или <what>
    if (maybe_version or maybe_what) and args:
        alias = args.pop(0).lower()

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
                for version in get_settings(name)["versions"]:
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

        elif options["what"] != AvailabilityEnum.PROHIBITED:
            whats = resolve_whats(name, alias)

    # Третий аргумент <what>
    if maybe_what and args and not whats:
        whats = args.pop(0).lower()
        whats = resolve_whats(name, whats)

    if not versions:
        versions = [None]

    if not whats:
        whats = [None]

    commands = []
    for version in versions:
        for what in whats:
            commands.append(Command(name, version, what, args))
    return commands


def run(args: list[str]):
    try:
        for command in parse_cmd_args(args):
            command.run()

    except ParameterAvailabilityException as e:
        name: str = e.command.name
        settings: dict = get_settings(name)
        options: dict = settings["options"]

        # Если для сущности параметр версии возможен
        if options["version"] != AvailabilityEnum.PROHIBITED:
            supported_versions = ", ".join(sorted(settings["versions"]))
            print(f"Поддерживаемые версии: {supported_versions}")
            return

        # Если для сущности параметр what возможен
        if options["what"] != AvailabilityEnum.PROHIBITED:
            supported_whats = ", ".join(sorted(settings["whats"]))
            print(f"Поддерживаемые <what>: {supported_whats}")
            return

        print(e)

    except GoException as e:
        # Если передан флаг отладки
        show_exception_flag = "-e"
        if args[-1].lower().startswith(show_exception_flag):
            print(traceback.format_exc())
        else:
            print(e)
            print(f"Повтори с флагом {show_exception_flag} - чтобы увидеть ошибку с стеком")


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
