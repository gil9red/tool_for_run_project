#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import enum
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import psutil

from core import (
    AvailabilityEnum,
    ParameterAvailabilityException,
    GoException,
    UnknownNameException,
    UnknownWhatException,
    get_similar_value,
    is_like_a_short_version,
)
from core.jenkins import do_check_jenkins_job, JenkinsJobCheckException
from core.kill import (
    kill_servers,
    kill_explorers,
    kill_designers,
    get_processes,
    is_server,
    is_explorer,
    is_designer,
)
from core.svn.find_release_version import find_release_version
from core.svn.get_last_release_version import (
    get_last_release_version as get_last_release_version_svn,
)
from core.svn.search_by_versions import search as search_by_versions
from settings import get_project, get_path_by_name
from third_party.from_ghbdtn import from_ghbdtn


WhatValue = str | list[str, str | Callable] | dict | Callable | None


def run_file(file_name: str):
    dir_file_name = os.path.dirname(file_name)
    file_name = os.path.normpath(file_name)

    print(f"Запуск: {file_name!r}")

    # Move to active dir
    os.chdir(dir_file_name)

    # Run
    os.startfile(file_name)


def open_dir(path: str):
    if os.path.isfile(path):
        dir_file_name = os.path.dirname(path)
    else:
        dir_file_name = path

    print(f"Открытие: {dir_file_name!r}")

    # Open
    os.startfile(dir_file_name)


@dataclass
class Command:
    name: str
    version: str | None = None
    what: str | None = None
    args: list[str] | None = None

    def __post_init__(self):
        if self.args is None:
            self.args = []

    def _check_parameter(self, param: str):
        settings = get_project(self.name)

        value = getattr(self, param)
        settings_param = settings["options"][param]
        if settings_param == AvailabilityEnum.REQUIRED:
            if not value:
                raise ParameterAvailabilityException(self, param, settings_param)

        elif settings_param == AvailabilityEnum.PROHIBITED:
            if value:
                raise ParameterAvailabilityException(self, param, settings_param)

    def run(self):
        settings: dict = get_project(self.name)
        options: dict = settings["options"]

        if options["version"] == AvailabilityEnum.OPTIONAL and not self.version:
            self.version = resolve_version(
                self.name, options["default_version"]
            )

        settings_params = ["version", "what", "args"]
        for param in settings_params:
            self._check_parameter(param)

        # Если по <name> указывается файл, то сразу его и запускаем
        path: str = get_path_by_name(self.name)
        value: WhatValue = get_file_by_what(self.name, self.what)

        # Если по <name> указывается файл, то сразу его и запускаем
        if (
            (os.path.isfile(path) and not self.what and not self.args)
            or all(
                options[param] == AvailabilityEnum.PROHIBITED
                for param in settings_params
            )
        ):
            run_file(path)
            return

        if self.version:
            path = get_similar_version_path(self.name, self.version)

        # Если в <whats> функция, вызываем её
        if callable(value):
            print(
                f"Запуск: {self.name} вызов {self.what!r}"
                + (f" ({', '.join(self.args)})" if self.args else "")
            )
            value(path, self.args, RunContext(self))
            return

        dir_file_name = get_similar_version_path(self.name, self.version)

        # Move to active dir
        os.chdir(dir_file_name)

        # Получение из аргументов
        if isinstance(value, dict):
            arg = self.args[0] if self.args else ""
            if not arg:
                arg = value["__default__"]

            value = value[arg]

        if isinstance(value, str):
            file_name = dir_file_name + "/" + value
            run_file(file_name)
            return

        description, command = value

        # Если функция - вызываем
        if callable(command):
            command(path, self.args, RunContext(self, description))
            return

        find_string = self.args[0] if self.args else ""
        command = command.format(path=dir_file_name, find_string=find_string)

        print(f"Запуск: {description} в {dir_file_name}")
        os.system(command)


@dataclass
class RunContext:
    command: Command
    description: str = ""


def run_path(path: str, args: list[str] | None = None, context: RunContext = None):
    if not args:
        print("Нужно задать маску файла")
        return

    file_mask = args[0]

    files = list(Path(path).glob(file_mask))
    if not files:
        print("Не найден файл")
        return

    if len(files) > 1:
        print(
            f"Маска файла должна соответствовать одному файлу.\nНайдено ({len(files)}):"
        )
        for name in files:
            print(f"    {name}")
        return

    file_name = str(files[0])
    run_file(file_name)


def open_path(path: str, args: list[str] | None = None, context: RunContext = None):
    if not context:
        raise GoException("Что-то пошло не так при вызове 'open' - context is None")

    command = context.command
    path = get_similar_version_path(command.name, command.version)
    open_dir(path)


def kill(path: str, args: list[str] | None = None, context: RunContext = None):
    pids = []

    # Если аргументы не заданы, то убиваем все процессы
    if not args:
        pids += kill_servers(path)
        pids += kill_explorers(path)
        pids += kill_designers(path)

    else:
        flags = []
        for arg in args:
            if arg.startswith("-"):
                arg = arg.strip("-").lower()
                flags += arg  # NOTE: "se" будут добавлены как "s" и "e"

        # -a - убиваем все сервера и проводники из всех папок
        if "a" in flags:
            pids += kill_servers()
            pids += kill_explorers()
            pids += kill_designers()
        else:
            if "s" in flags:
                pids += kill_servers(path)

            if "e" in flags:
                pids += kill_explorers(path)

            if "d" in flags:
                pids += kill_designers(path)

    if not pids:
        print("Не удалось найти процессы!")


def processes(path: str, args: list[str] | None = None, context: RunContext = None):
    class ProcessEnum(enum.Enum):
        Server = enum.auto()
        Explorer = enum.auto()
        Designer = enum.auto()

    type_by_processes = {
        ProcessEnum.Server: [],
        ProcessEnum.Explorer: [],
        ProcessEnum.Designer: [],
    }

    # all - показываем все процессы
    if args and args[0].lower().startswith("a"):
        path = None

    for p in get_processes(path):
        try:
            if is_server(p):
                type_by_processes[ProcessEnum.Server].append(p)
            elif is_explorer(p):
                type_by_processes[ProcessEnum.Explorer].append(p)
            elif is_designer(p):
                type_by_processes[ProcessEnum.Designer].append(p)
        except psutil.NoSuchProcess:
            pass

    for process_type, processes in type_by_processes.items():
        if not processes:
            continue

        print(f"{process_type.name} ({len(processes)}):")
        for p in processes:
            started_time = datetime.fromtimestamp(p.create_time())
            print(f"    #{p.pid}, запущено: {started_time:%d/%m/%Y %H:%M:%S}")

    if not any(type_by_processes.values()):
        print("Не удалось найти процессы!")


def get_last_release_version(
    path: str,
    args: list[str] | None = None,
    context: RunContext = None,
):
    command = context.command
    version = command.version

    # Значение в днях передается в аргументах
    last_days = 30
    if args and args[0].isdigit():
        last_days = int(args[0])

    url_svn_path = get_project(command.name)["svn_dev_url"]

    try:
        result = get_last_release_version_svn(
            version=version,
            last_days=last_days,
            url_svn_path=url_svn_path,
        )
    except Exception as e:
        result = str(e)

    print(f"Последняя версия релиза для {version}: {result}\n")


def find_release_versions(
    path: str,
    args: list[str] | None = None,
    context: RunContext = None,
):
    if context.command.version == "trunk":
        raise GoException("Команду нужно вызывать в релизных версиях!")

    if not args:
        raise GoException("Текст для поиска не указан!")

    text = args[0]

    # Значение в днях передается в аргументах
    last_days = 30
    if len(args) > 1 and args[1].isdigit():
        last_days = int(args[1])

    command = context.command
    version = command.version

    url_svn_path = get_project(command.name)["svn_dev_url"]

    try:
        result = find_release_version(
            text=text,
            version=version,
            last_days=last_days,
            url_svn_path=url_svn_path,
        )

    except Exception as e:
        result = str(e)

    print(f"Коммит с {text!r} в {version} попал в версию: {result}\n")


def find_versions(
    path: str,
    args: list[str] | None = None,
    context: RunContext = None,
):
    command = context.command

    if not args:
        raise GoException("Текст для поиска не указан!")

    text = args[0]

    # Значение в днях передается в аргументах
    last_days = 30
    if len(args) > 1 and args[1].isdigit():
        last_days = int(args[1])

    url_svn_path = get_project(command.name)["svn_dev_url"]

    try:
        versions = search_by_versions(
            text=text,
            last_days=last_days,
            url_svn_path=url_svn_path,
        )
        result = ", ".join(versions)

    except Exception as e:
        result = str(e)

    print(f"Строка {text!r} встречается в версиях: {result}")


def manager_up(path: str, _: list[str] | None = None, context: RunContext = None):
    path = Path(path)

    # NOTE: "C:\DEV__RADIX\manager\manager\bin\manager.cmd" -> "C:\DEV__RADIX\manager"
    root_dir = path.parent.parent.parent
    path_from = root_dir / "radix_manager/distrib"
    files = list(path_from.rglob("*.zip"))
    if not files:
        print(f"Не найдены файлы в {path_from}")
        return

    path_to = root_dir / "optt_manager/upgrades"
    print(f"Перемещение файлов в {path_to}:")

    for file in files:
        print(f"    File: {file.name}")

        new_file = path_to / file.name

        # Если файл уже есть, то удаляем его - мало ли в каком он состоянии
        if new_file.exists():
            new_file.unlink()

        shutil.move(file, new_file)


def manager_clean(path: str, _: list[str] | None = None, context: RunContext = None):
    path = Path(path)

    # NOTE: "C:\DEV__RADIX\manager\manager\bin\manager.cmd" -> "C:\DEV__RADIX\manager"
    root_dir = path.parent.parent.parent
    path_from = root_dir / "optt_manager/upgrades.backup"
    files = list(path_from.rglob("*.zip"))
    if not files:
        print(f"Не найдены файлы в {path_from}")
        return

    print(f"Удаление файлов из {path_from}:")
    for file in files:
        print(f"    Файл: {file.name}")
        file.unlink()


def svn_update(path: str, args: list[str] | None = None, context: RunContext = None):
    force = False

    # force - обновляемся, даже если сборка сломана
    if args and "-f" in args:
        force = True

    command = context.command
    settings = get_project(command.name)

    jenkins_url = settings.get("jenkins_url")
    if jenkins_url:
        try:
            do_check_jenkins_job(jenkins_url, command.version)
        except JenkinsJobCheckException as e:
            if not force:
                text = "Чтобы все-равно загрузить повторите с аргументом -f"
                print(f"{e}\n\n{text}")
                return

    command_svn = r'start /b "" TortoiseProc /command:update /path:"{path}"'
    command_svn = command_svn.format(path=path)

    title = f"{context.description} в {path}".strip()

    print(f"Запуск: {title}")
    os.system(command_svn)


def resolve_whats(name: str, alias: str | None) -> list[str]:
    items = []
    if not alias:
        return items

    supported = list(get_project(name)["whats"])
    shadow_supported = {from_ghbdtn(x): x for x in supported}

    for alias_what in alias.split("+"):
        # Поиск среди списка
        what = get_similar_value(alias_what, supported)
        if not what:
            # Попробуем найти среди транслитерованных
            what = get_similar_value(alias_what, shadow_supported)
            if not what:
                raise UnknownWhatException(alias_what, supported)

            # Если удалось найти
            what = shadow_supported[what]

        items.append(what)

    return items


def resolve_version(name: str, alias: str, versions: list[str] | None = None) -> str:
    settings = get_project(name)

    supported = versions
    if not supported:
        supported = settings["versions"]

    shadow_supported = {from_ghbdtn(x): x for x in supported}

    # Если короткая версия, нужно ее расширить, добавив основание версии
    if is_like_a_short_version(alias):
        base_version = settings.get("base_version")
        if not base_version:
            text = (
                f'Атрибут "base_version", используемый с короткой версией (="{alias}"), '
                f'должен быть определен в SETTINGS для "{name}"'
            )
            raise GoException(text)

        # Составление полной версии
        alias = base_version + alias

    # Поиск среди списка
    version = get_similar_value(alias, supported)
    if not version:
        # Попробуем найти среди транслитерованных
        version = get_similar_value(alias, shadow_supported)
        if not version:
            raise UnknownNameException(alias, supported)

        # Если удалось найти
        version = shadow_supported[version]

    return version


def get_file_by_what(name: str, alias: str | None) -> WhatValue:
    whats = resolve_whats(name, alias)
    if not whats:
        return
    what = whats[0]
    return get_project(name)["whats"][what]


def get_similar_version_path(name: str, version: str) -> str:
    supported = get_project(name)["versions"]
    version = resolve_version(name, version, supported)
    return supported[version]
