#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
from enum import Enum, auto
from typing import Iterable

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


class UnknownWhatException(GoException):
    def __init__(self, what: str, supported: Iterable[str]):
        self.what = what
        self.supported = list(sorted(supported))

        super().__init__(
            f"Неизвестное действие {self.what!r}, поддержано: {self.supported}"
        )


class UnknownVersionException(GoException):
    def __init__(self, version: str, supported: Iterable[str]):
        self.version = version
        self.supported = list(supported)

        super().__init__(
            f"Неизвестная версия {self.version!r}, поддержано: {self.supported}"
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


def get_similar_value(alias: str, items: Iterable) -> str | None:
    if alias in items:
        return alias

    # Ищем похожие ключи по начальной строке
    keys = [key for key in items if key.startswith(alias)]

    # Нашли одну вариацию - подходит
    if len(keys) == 1:
        return keys[0]


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
