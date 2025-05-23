#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import os
import shutil

from pathlib import Path
from unittest import TestCase


DIR: Path = Path(__file__).parent.resolve()

DIR_ENV: Path = DIR / "env"
DIR_ENV.mkdir(parents=True, exist_ok=True)

# TODO: Тут и создать папку с файлами для тестовой настройки
# TODO: Заполнить пути от текущего пути
SETTINGS_TEMPLATE_JSON: str = r"""
{
    "__radix_base": {
        "options": {
            "version": "${AvailabilityEnum.OPTIONAL}",
            "what": "${AvailabilityEnum.REQUIRED}",
            "args": "${AvailabilityEnum.OPTIONAL}",
            "default_version": "trunk"
        },
        "whats": {
            "designer": "!!designer.cmd",
            "explorer": "!!explorer.cmd",
            "server": {
                "__default__": "ora",
                "ora": "!!server.cmd",
                "pg": "!!server-postgres.cmd"
            },
            "compile": "!build_ads__pause.bat",
            "build": "!build_kernel__pause.cmd",
            "update": [
                "svn update",
                "${commands.svn_update}"
            ],
            "log": [
                "svn log",
                "start /b \"\" TortoiseProc /command:log /path:\"{path}\" /findstring:\"{find_string}\""
            ],
            "cleanup": [
                "svn cleanup",
                "start /b \"\" TortoiseProc /command:cleanup /path:\"{path}\" /cleanup /nodlg /closeonend:2"
            ],
            "revert": [
                "svn revert",
                "start /b \"\" TortoiseProc /command:revert /path:\"{path}\""
            ],
            "modifications": [
                "svn show modifications dialog",
                "start /b \"\" TortoiseProc /command:repostatus /path:\"{path}\""
            ],
            "run": "${commands.run_path}",
            "open": "${commands.open_path}",
            "kill": "${commands.kill}",
            "processes": "${commands.processes}",
            "get_last_release_version": "${commands.get_last_release_version}",
            "find_release_versions": "${commands.find_release_versions}",
            "find_versions": "${commands.find_versions}",
            "trace": "!!trace_viewer.cmd"
        },
        "vars": {
            "URL_JENKINS": "http://10.77.204.68:8080"
        }
    },
    "radix": {
        "base": "__radix_base",
        "path": "C:/DEV__RADIX",
        "base_version": "2.1."
    },
    "tx": {
        "base": "__radix_base",
        "path": "C:/DEV__TX",
        "base_version": "3.2.",
        "jenkins_url": "${self['tx']['vars']['URL_JENKINS'] + '/job/assemble_tx/branch={version},label=lightweight/lastBuild/api/json?tree=result,timestamp,url'}",
        "svn_dev_url": "svn+cplus://svn2.compassplus.ru/twrbs/trunk/dev"
    },
    "optt": {
        "base": "__radix_base",
        "path": "C:/DEV__OPTT",
        "base_version": "2.1.",
        "jenkins_url": "${self['optt']['vars']['URL_JENKINS'] + '/job/OPTT_{version}_build/lastBuild/api/json?tree=result,timestamp,url'}",
        "svn_dev_url": "svn+cplus://svn2.compassplus.ru/twrbs/csm/optt/dev"
    },
    "__simple_base": {
        "options": {
            "version": "${AvailabilityEnum.PROHIBITED}",
            "what": "${AvailabilityEnum.PROHIBITED}",
            "args": "${AvailabilityEnum.PROHIBITED}"
        }
    },
    "manager": {
        "base": "__simple_base",
        "path": "C:/DEV__RADIX/manager/manager/bin/manager.cmd",
        "options": {
            "what": "${AvailabilityEnum.OPTIONAL}"
        },
        "whats": {
            "up": "${commands.manager_up}",
            "clean": "${commands.manager_clean}"
        }
    },
    "doc": {
        "base": "__simple_base",
        "path": "C:/Program Files (x86)/DocFetcher/DocFetcher.exe"
    },
    "specifications": {
        "base": "__simple_base",
        "path": "C:/DOC/Specifications"
    }
}
"""

PATH_TEST_SETTINGS: Path = DIR_ENV / "test-settings.json"
PATH_TEST_SETTINGS.write_text(SETTINGS_TEMPLATE_JSON, encoding="utf-8")

# NOTE: Установка переменной окружения до импорта модулей, который явно или не явно импортируют модуль settings.py
os.environ["PATH_SETTINGS"] = str(PATH_TEST_SETTINGS)

from core.commands import resolve_whats, resolve_version, get_similar_version_path
from core import is_like_a_version

import settings
from settings import resolve_name

from third_party.from_ghbdtn import from_ghbdtn


settings.run_settings_preprocess()
SETTINGS = settings.SETTINGS


# TODO:
# class TestCommon(TestCase):
#     def test_resolve_name(self):
#         for k in SETTINGS:
#             assert resolve_name(k) == k
#             assert resolve_name(from_ghbdtn(k)) == k
#         assert resolve_name("t") == "tx"
#         assert resolve_name("tx") == "tx"
#         assert resolve_name("еч") == "tx"
#         assert resolve_name("щзе") == "optt"
#         assert resolve_name("o") == "optt"
#         assert resolve_name("optt") == "optt"


resolve_what = lambda alias: resolve_whats("tx", alias)[0]

for k in SETTINGS["tx"]["whats"]:
    assert resolve_what(k) == k
    assert resolve_what(from_ghbdtn(k)) == k
assert resolve_what("d") == "designer"
assert resolve_what("в") == "designer"
assert resolve_what("вуы") == "designer"
assert resolve_what("e") == "explorer"
assert resolve_what("b") == "build"

# TODO: Зависит от окружения - без папок локально не работает
assert resolve_version("tx", "trunk") == "trunk"
assert resolve_version("tx", "tr") == "trunk"
assert resolve_version("еч", "trunk") == "trunk"
assert resolve_version("optt", "trunk") == "trunk"
assert resolve_version("щзе", "trunk") == "trunk"
assert resolve_version("tx", "екгтл") == "trunk"
assert resolve_version("tx", "ек") == "trunk"

# TODO: Зависит от окружения - без папок локально не работает
assert get_similar_version_path("tx", "trunk")
assert get_similar_version_path("tx", "tru")
assert get_similar_version_path("tx", "екгтл")
assert get_similar_version_path("tx", "екг")
assert get_similar_version_path("еч", "trunk")
assert get_similar_version_path("еч", "екгтл")

assert is_like_a_version("trunk")
assert is_like_a_version("екгтл")
assert is_like_a_version("екг")
assert is_like_a_version("trunk-екгтл")
assert is_like_a_version("trunk,екгтл")
assert is_like_a_version("3.2.22-trunk")
assert is_like_a_version("3.2.22-екгтл")
assert is_like_a_version("3.2.22")
assert is_like_a_version("3.2.22.10")

shutil.rmtree(DIR_ENV)
