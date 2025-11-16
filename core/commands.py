#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import enum
import os
import shutil
import sys

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

import psutil

from core import (
    AvailabilityEnum,
    ParameterAvailabilityException,
    GoException,
    UnknownActionException,
    UnknownVersionException,
    resolve_alias,
    is_like_a_short_version,
    radix_update_compile_designer,
    _open_path,
    run_file,
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
from core.utils import run_command_in_new_terminal
from core.svn.find_release_version import find_release_version
from core.svn.get_age import get_age as svn_get_age
from core.svn.get_last_release_version import (
    get_last_release_version as get_last_release_version_svn,
)
from core.svn.search_by_versions import search as search_by_versions
from settings import get_project, get_path_by_name

from third_party.get_project_versions import process as run_get_project_versions


ActionValue = str | list[str, str | Callable] | dict | Callable | None


@dataclass
class Command:
    name: str
    version: str | None = None
    action: str | None = None
    args: list[str] = field(default_factory=list)

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

    def is_forced(self) -> bool:
        return self.args and "-f" in self.args

    def run(self):
        settings: dict = get_project(self.name)
        options: dict = settings["options"]

        settings_params = ["version", "action", "args"]
        for param in settings_params:
            self._check_parameter(param)

        if self.version:
            path: str = get_similar_version_path(self.name, self.version)
        else:
            path_value: str | list[str] = get_path_by_name(self.name)
            if isinstance(path_value, str):
                path: str = path_value
            else:
                if not path_value:
                    raise GoException(
                        f"Пустое значение 'path' в настройках {self.name!r}"
                    )

                path: str = path_value[0]

        # Если по <name> указывается файл, то сразу его и запускаем
        if (Path(path).is_file() and not self.action and not self.args) or all(
            options[param] == AvailabilityEnum.PROHIBITED for param in settings_params
        ):
            run_file(path)
            return

        value: ActionValue = get_file_by_action(self.name, self.action)

        # Если в <actions> функция, вызываем её
        if callable(value):
            print(
                f"Запуск: {self.name} вызов {self.action!r}"
                + (f" ({', '.join(self.args)})" if self.args else "")
            )
            value(RunContext(self, path=path))
            return

        dir_file_name: str = get_similar_version_path(self.name, self.version)

        # Move to active dir
        os.chdir(dir_file_name)

        # Получение из аргументов
        if isinstance(value, dict):
            arg: str = self.args[0]
            value: str = value[arg]

        if isinstance(value, str):
            file_name = dir_file_name + "/" + value
            run_file(file_name)
            return

        description, command = value

        # Если функция - вызываем
        if callable(command):
            command(RunContext(self, path=path, description=description))
            return

        find_string: str = " ".join(self.args) if self.args else ""
        command: str = command.format(path=dir_file_name, find_string=find_string)

        print(f"Запуск: {description} в {dir_file_name}")
        os.system(command)


@dataclass
class RunContext:
    command: Command
    path: str
    description: str = ""


def run_path(context: RunContext):
    path: str = context.path
    args: list[str] = context.command.args

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


def open_path_dir(context: RunContext):
    path_dir: Path = Path(context.path).resolve()
    if path_dir.is_file():
        path_dir = path_dir.parent

    print(f"Открытие папки: {str(path_dir)!r}")

    _open_path(str(path_dir))


def kill(context: RunContext):
    path: str = context.path
    args: list[str] = context.command.args

    pids: list[int] = []

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


def processes(context: RunContext):
    path: str = context.path
    args: list[str] = context.command.args

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
        path: str | None = None

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


def svn_get_last_release_version(context: RunContext):
    command = context.command
    args: list[str] = command.args
    version: str | None = command.version

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

    print(f"Последняя версия релиза для {version} (за {last_days} дней): {result}\n")


def svn_find_release_versions(context: RunContext):
    if context.command.version == "trunk":
        raise GoException("Команду нужно вызывать в релизных версиях!")

    args: list[str] = context.command.args
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
        result: str = find_release_version(
            text=text,
            version=version,
            last_days=last_days,
            url_svn_path=url_svn_path,
        )

    except Exception as e:
        raise GoException(str(e))

    print(f"Коммит с {text!r} (за {last_days} дней) в {version} попал в версию: {result}\n")


def svn_where(context: RunContext):
    command = context.command

    args: list[str] = command.args
    if not args:
        raise GoException("Текст для поиска не указан!")

    text = args[0]

    # Значение в днях передается в аргументах
    last_days = 30
    if len(args) > 1 and args[1].isdigit():
        last_days = int(args[1])

    url_svn_path = get_project(command.name)["svn_dev_url"]

    versions: list[str] = search_by_versions(
        text=text,
        last_days=last_days,
        url_svn_path=url_svn_path,
    )
    result = ", ".join(versions)

    print(f"Строка {text!r} (за {last_days} дней) встречается в версиях: {result}")


def svn_get_age_of_version(context: RunContext):
    command = context.command
    version: str | None = command.version

    if version == "trunk" and not command.is_forced():
        print(
            f"Для версии {version!r} операция будет выполняться слишком долго.\n"
            f"Чтобы все-равно выполнить, повторите с аргументом -f"
        )
        return

    url_svn_path = get_project(command.name)["svn_dev_url"]
    result: str = svn_get_age(
        version=version,
        url_svn_path=url_svn_path,
    )

    print(f"Возраст версии {version!r}:\n{result}\n")


def get_versions_of_version(context: RunContext):
    run_get_project_versions(Path(context.path))


def manager_up(context: RunContext):
    path = Path(context.path)

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


def manager_clean(context: RunContext):
    path = Path(context.path)

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


def svn_update(context: RunContext):
    path: str = context.path
    command = context.command

    settings = get_project(command.name)

    jenkins_url = settings.get("jenkins_url")
    if jenkins_url:
        try:
            do_check_jenkins_job(jenkins_url, command.version)
        except JenkinsJobCheckException as e:
            # Обновление, даже если сборка сломана
            if not command.is_forced():
                text = "Чтобы все-равно загрузить повторите с аргументом -f"
                print(f"{e}\n\n{text}")
                return

    command_svn = r'start /b "" TortoiseProc /command:update /path:"{path}"'
    command_svn = command_svn.format(path=path)

    title = f"{context.description} в {path}".strip()

    print(f"Запуск: {title}")
    os.system(command_svn)


def run_radix_update_compile_designer(context: RunContext):
    path: str = context.path
    script_path: str = radix_update_compile_designer.__file__

    args: list[str] = [sys.executable, script_path, path]
    run_command_in_new_terminal(args)


def resolve_actions(name: str, alias: str | None) -> list[str]:
    items = []
    if not alias:
        return items

    supported: list[str] = list(get_project(name)["actions"])

    for alias_action in alias.split("+"):
        action: str = resolve_alias(
            alias=alias_action,
            supported=supported,
            unknown_alias_exception_cls=UnknownActionException,
        )
        items.append(action)

    return items


def resolve_version(name: str, alias: str) -> str:
    settings: dict = get_project(name)

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
        alias = base_version.format(number=alias)

    return resolve_alias(
        alias=alias,
        supported=settings["versions"],
        unknown_alias_exception_cls=UnknownVersionException,
    )


def get_file_by_action(name: str, alias: str | None) -> ActionValue:
    actions = resolve_actions(name, alias)
    if not actions:
        return
    action = actions[0]
    return get_project(name)["actions"][action]


def get_similar_version_path(name: str, version: str) -> str:
    supported = get_project(name)["versions"]
    version = resolve_version(name, version)
    return supported[version]
