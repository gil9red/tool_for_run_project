#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import os
import re
import subprocess
import sys

from enum import Enum, auto
from pathlib import Path
from typing import Iterable, Type

from third_party.from_ghbdtn import from_ghbdtn


class AvailabilityEnum(Enum):
    OPTIONAL = auto()
    REQUIRED = auto()
    PROHIBITED = auto()


class GoException(Exception):
    pass


class UnknownNameException(GoException):
    def __init__(self, name: str, supported: Iterable[str]):
        self.name = name
        self.supported = list(sorted(supported))

        super().__init__(f"Неизвестное имя {self.name!r}, поддержано: {self.supported}")


class UnknownActionException(GoException):
    def __init__(self, action: str, supported: Iterable[str]):
        self.action = action
        self.supported = list(sorted(supported))

        super().__init__(
            f"Неизвестное действие {self.action!r}, поддержано: {self.supported}"
        )


class UnknownVersionException(GoException):
    def __init__(self, version: str, supported: Iterable[str]):
        self.version = version
        self.supported = list(supported)

        super().__init__(
            f"Неизвестная версия {self.version!r}, поддержано: {self.supported}"
        )


class UnknownArgException(GoException):
    def __init__(self, arg: str, supported: Iterable[str]):
        self.arg = arg
        self.supported = list(supported)

        super().__init__(
            f"Неизвестный аргумент {self.arg!r}, поддержано: {self.supported}"
        )


class ParameterMissingException(GoException):
    def __init__(self, name: str, param: str):
        self.name = name
        self.param = param

        super().__init__(
            f"Для {self.name!r} значение <{self.param}> не должно быть установлено!"
        )


class ParameterAvailabilityException(GoException):
    def __init__(self, command: "Command", param: str, availability: AvailabilityEnum):
        if availability == AvailabilityEnum.REQUIRED:
            post_fix = "должно быть установлено!"
        elif availability == AvailabilityEnum.PROHIBITED:
            post_fix = "не может быть установлено!"
        else:
            raise GoException(f"Не поддерживается: {availability}!")

        self.command = command
        self.param = param
        self.availability = availability

        super().__init__(
            f"Для {self.command.name!r} значение <{self.param}> " + post_fix
        )


def get_similar_value(alias: str, items: Iterable[str]) -> str | None:
    alias_lower: str = alias.lower()

    # Если совпало со значением как есть
    for key in map(str.lower, items):
        if alias_lower == key:
            return key

    # Ищем похожие ключи по начальной строке
    keys: list[str] = [key for key in items if key.lower().startswith(alias_lower)]

    # Нашли одну вариацию - подходит
    # TODO: Предусмотреть ошибку, мол нашлось несколько вариантов: xxx, yyy, aaa
    if len(keys) == 1:
        return keys[0]

    return


def resolve_alias(
    alias: str,
    supported: list[str],
    unknown_alias_exception_cls: Type[
        UnknownArgException
        | UnknownNameException
        | UnknownActionException
        | UnknownVersionException
    ],
) -> str:
    shadow_supported: dict[str, str] = {from_ghbdtn(x): x for x in supported}

    key: str | None = get_similar_value(alias, supported)
    if key:
        return key

    # Попробуем найти среди транслитерованных
    key = get_similar_value(alias, shadow_supported)
    if not key:
        raise unknown_alias_exception_cls(alias, supported)

    return shadow_supported[key]


def is_like_a_short_version(value: str) -> bool:
    # Вариант .isdigit() для коротких версий, не 3.2.25, а 25
    return value.isdigit()


def is_like_a_version(value: str) -> bool:
    trunk = "trunk"
    trunk_invert = from_ghbdtn(trunk)  # "trunk" -> "екгтл"
    return (
        trunk in value  # Для файлов
        or bool(get_similar_value(value, [trunk, trunk_invert]))
        or bool(re.search(r"\d+(\.\d+)+", value))
        or is_like_a_short_version(value)
        or "-" in value  # Example: "23-25" or "23-trunk"
        or "," in value  # Example: "23,24,25" or "23,24,25,trunk"
    )


def _open_path(file_name: str, dir_file_name: str | None = None):
    if sys.platform == "win32":
        os.startfile(file_name, cwd=dir_file_name)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, file_name], cwd=dir_file_name)


def run_file(file_name: Path | str):
    if isinstance(file_name, str):
        file_name = Path(file_name)

    file_name = file_name.resolve()
    print(f"Запуск: {str(file_name)!r}")

    dir_file_name = file_name.parent
    _open_path(str(file_name), str(dir_file_name))
