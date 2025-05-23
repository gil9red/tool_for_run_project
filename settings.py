#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import copy
import json
import re
import os

from pathlib import Path
from typing import Any, Callable

from core import (
    AvailabilityEnum,
    is_like_a_version,
    get_similar_value,
    UnknownNameException,
)
from third_party.from_ghbdtn import from_ghbdtn


if path_settings_value := os.getenv("PATH_SETTINGS"):
    PATH_SETTINGS = Path(path_settings_value).resolve()
else:
    PATH_SETTINGS = Path(__file__).parent.resolve() / "settings.json"

__SETTINGS = json.loads(PATH_SETTINGS.read_text(encoding="utf-8"))


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


# SOURCE: https://github.com/gil9red/SimplePyScripts/blob/c8639e909c2ad48c127e11595396f148d5970e10/walk_dict.py
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


PATTERN_CODE_BLOCK = re.compile(r"^\$\{(.+)}$")


def walk_dir_run_code(_: Any, v: Any, settings: dict[str, Any]) -> Any:
    # NOTE: Импортировать нужно тут - глобально нельзя
    import core.commands

    global_vars: dict[str, Any] = {
        "AvailabilityEnum": core.AvailabilityEnum,
        "commands": core.commands,
        "self": settings,
    }

    match v:
        # Или строка, или список из двух строк
        case (str() as value) | [str(), str() as value]:
            if m := PATTERN_CODE_BLOCK.match(value):
                eval_str = m.group(1)
                try:
                    value = eval(eval_str, global_vars)
                except Exception:
                    raise Exception(f"Error on eval {eval_str!r}, original {value!r}")

                if isinstance(v, list):
                    v[1] = value
                else:
                    v = value

    return v


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

    walk_dict(new_settings, lambda k, v: walk_dir_run_code(k, v, new_settings))

    return new_settings


SETTINGS = __SETTINGS


def run_settings_preprocess():
    global SETTINGS
    SETTINGS = settings_preprocess(__SETTINGS)


def get_project(name: str) -> dict:
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
    settings = get_project(name)
    return settings["path"]
