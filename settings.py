#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import copy
from pathlib import Path
from typing import Any, Callable

from core import (
    AvailabilityEnum,
    is_like_a_version,
    get_similar_value,
    UnknownNameException,
)
from third_party.from_ghbdtn import from_ghbdtn


# from core.commands import (
#     get_versions_by_path,
#     _run_path,
#     _kill,
#     _processes,
#     _get_last_release_version,
#     _find_release_versions,
#     _find_versions,
#     _manager_up,
#     _manager_clean,
#     _server,
#     _svn_update,
# )


# SOURCE: https://stackoverflow.com/a/20666342/5909792
def merge_dicts(source: dict, destination: dict) -> dict:
    for key, value in source.items():
        if isinstance(value, dict):
            # Get node or create one
            node = destination.setdefault(key, dict())
            merge_dicts(value, node)
        else:
            destination[key] = value

    return destination


# TODO:
# print(eval("__import__('core.commands', fromlist=['commands'])._svn_update"))
#
# quit()


# TODO:
def walk_dict(
    node: dict,
    value_process_func: Callable[[Any, Any], Any] | None = None,
):
    for key, value in node.items():
        if value_process_func:
            value = value_process_func(key, value)
            node[key] = value

        if isinstance(value, dict):
            walk_dict(value, value_process_func)


__SETTINGS = {
    "__radix_base": {
        "options": {
            "version": AvailabilityEnum.OPTIONAL,
            "what": AvailabilityEnum.REQUIRED,
            "args": AvailabilityEnum.OPTIONAL,
            "default_version": "trunk",
        },
        "whats": {
            "designer": "!!designer.cmd",
            "explorer": "!!explorer.cmd",
            "server": (
                "server",
                # TODO: "${__import__('core.commands')._server}"
                # TODO: Проверить на callable
                "${__import__('core.commands', fromlist=['commands'])._server}",
            ),
            "compile": "!build_ads__pause.bat",
            "build": "!build_kernel__pause.cmd",
            "update": (
                "svn update",
                "${__import__('core.commands', fromlist=['commands'])._svn_update}",
            ),
            "log": (
                "svn log",
                r'start /b "" TortoiseProc /command:log /path:"{path}" /findstring:"{find_string}"',
            ),
            "cleanup": (
                "svn cleanup",
                'start /b "" TortoiseProc /command:cleanup /path:"{path}" /cleanup /nodlg /closeonend:2',
            ),
            "revert": (
                "svn revert",
                'start /b "" TortoiseProc /command:revert /path:"{path}"',
            ),
            "modifications": (
                "svn show modifications dialog",
                'start /b "" TortoiseProc /command:repostatus /path:"{path}"',
            ),
            "run": "${__import__('core.commands', fromlist=['commands'])._run_path}",
            "kill": "${__import__('core.commands', fromlist=['commands'])._kill}",
            "processes": "${__import__('core.commands', fromlist=['commands'])._processes}",
            "get_last_release_version": "${__import__('core.commands', fromlist=['commands'])._get_last_release_version}",
            "find_release_versions": "${__import__('core.commands', fromlist=['commands'])._find_release_versions}",
            "find_versions": "${__import__('core.commands', fromlist=['commands'])._find_versions}",
            "trace": "!!trace_viewer.cmd",
        },
    },
    "radix": {
        "base": "__radix_base",
        "path": "C:/DEV__RADIX",
        "base_version": "2.1.",
    },
    "tx": {
        "base": "__radix_base",
        "path": "C:/DEV__TX",
        "base_version": "3.2.",
        "jenkins_url": (
            "{URL_JENKINS}/job/assemble_tx/branch={version},label=lightweight/lastBuild/api/json?tree=result,timestamp"
        ),
        "svn_dev_url": "svn+cplus://svn2.compassplus.ru/twrbs/trunk/dev",
    },
    "optt": {
        "base": "__radix_base",
        "path": "C:/DEV__OPTT",
        "base_version": "2.1.",
        "jenkins_url": "{URL_JENKINS}/job/OPTT_{version}_build/lastBuild/api/json?tree=result,timestamp",
        "svn_dev_url": "svn+cplus://svn2.compassplus.ru/twrbs/csm/optt/dev",
    },
    "__simple_base": {
        "options": {
            "version": AvailabilityEnum.PROHIBITED,
            "what": AvailabilityEnum.PROHIBITED,
            "args": AvailabilityEnum.PROHIBITED,
        }
    },
    "manager": {
        "base": "__simple_base",
        "path": "C:/DEV__RADIX/manager/manager/bin/manager.cmd",
        "options": {
            "what": AvailabilityEnum.OPTIONAL,
        },
        "whats": {
            "up": "${__import__('core.commands', fromlist=['commands'])._manager_up}",
            "clean": "${__import__('core.commands', fromlist=['commands'])._manager_clean}",
        },
    },
    "doc": {
        "base": "__simple_base",
        "path": "C:/Program Files (x86)/DocFetcher/DocFetcher.exe",
    },
    "specifications": {
        "base": "__simple_base",
        "path": "C:/DOC/Specifications",
    },
}


def get_versions_by_path(path: str) -> dict[str, str]:
    version_by_path = dict()

    dir_path = Path(path)

    if dir_path.is_dir():
        for path in dir_path.iterdir():
            if path.is_dir() and is_like_a_version(path.name):
                version_by_path[path.name] = str(path)

    return version_by_path


def settings_preprocess(settings: dict[str, dict]) -> dict[str, dict]:
    new_settings = dict()

    # Update from bases
    for name, values in settings.items():
        if "base" in values:
            # Removing base name
            base_name = values.pop("base")
            base_values = settings[base_name]
            new_settings[name] = copy.deepcopy(base_values)

        if name not in new_settings:
            new_settings[name] = dict()

        merge_dicts(values, new_settings[name])

        if (
            "path" in new_settings[name]
            and new_settings[name]["options"]["version"] != AvailabilityEnum.PROHIBITED
        ):
            path = new_settings[name]["path"]
            new_settings[name]["versions"] = get_versions_by_path(path)

    # Removing private names
    private_names = [name for name in new_settings if name.startswith("__")]
    for name in private_names:
        new_settings.pop(name)

    # TODO: Сделать проход до Update from bases
    # TODO:
    import re

    pattern = re.compile(r"^\$\{(.+?)}$")

    # TODO: Ловить ошибки с eval и выводить что туда попало
    def foo(k, v):
        if isinstance(v, str):
            m = pattern.match(v)
            if m:
                return eval(m.group(1))
        if isinstance(v, tuple) and len(v) == 2 and isinstance(v[1], str):
            m = pattern.match(v[1])
            if m:
                return eval(m.group(1))
        return v

    walk_dict(new_settings, foo)

    return new_settings


SETTINGS = __SETTINGS


def run_settings_preprocess():
    global SETTINGS
    SETTINGS = settings_preprocess(__SETTINGS)


def get_settings(name: str) -> dict:
    name = resolve_name(name)
    return SETTINGS[name]


def resolve_name(alias: str) -> str:
    supported = list(SETTINGS)
    shadow_supported = {from_ghbdtn(x): x for x in supported}

    # Поиск среди списка
    name = get_similar_value(alias, supported)
    if not name:
        # Попробуем найти среди транслитерованных
        name = get_similar_value(alias, shadow_supported)
        if not name:
            raise UnknownNameException(alias, supported)

        # Если удалось найти
        name = shadow_supported[name]

    return name


def get_path_by_name(name: str) -> str:
    settings = get_settings(name)
    return settings["path"]
