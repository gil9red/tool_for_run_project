#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import json
import os

from pathlib import Path
from unittest import TestCase


DIR: Path = Path(__file__).parent.resolve()

DIR_ENV: Path = DIR / "env"
DIR_ENV.mkdir(parents=True, exist_ok=True)

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
            "server": {
                "__default__": "ora",
                "ora": "!!server.cmd",
                "pg": "!!server-postgres.cmd"
            },
            "update": [
                "svn update",
                "${commands.svn_update}"
            ],
            "log": [
                "svn log",
                "start /b \"\" TortoiseProc /command:log /path:\"{path}\" /findstring:\"{find_string}\""
            ]
        },
        "vars": {
            "URL_JENKINS": "http://127.0.0.1:8080"
        }
    },
    "tx": {
        "base": "__radix_base",
        "path": "C:/DEV__TX",
        "base_version": "3.2.{number}",
        "jenkins_url": "${self['tx']['vars']['URL_JENKINS'] + '/job/assemble_tx/branch={version},label=lightweight/lastBuild/api/json?tree=result,timestamp,url'}",
        "svn_dev_url": "svn://127.0.0.1/tx/dev/trunk"
    },
    "optt": {
        "base": "__radix_base",
        "path": "C:/DEV__OPTT",
        "base_version": "2.1.{number}",
        "jenkins_url": "${self['optt']['vars']['URL_JENKINS'] + '/job/OPTT_{version}_build/lastBuild/api/json?tree=result,timestamp,url'}",
        "svn_dev_url": "svn://127.0.0.1/optt/dev/trunk"
    },
    "abc": {
        "base": "__radix_base",
        "path": "C:/DEV__ABC",
        "base_version": "4.1.{number}.10-dev",
        "jenkins_url": "${self['abc']['vars']['URL_JENKINS'] + '/job/ABC_{version}_build/lastBuild/api/json?tree=result,timestamp,url'}",
        "svn_dev_url": "svn://127.0.0.1/abc/dev/trunk"
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
    "file": {
        "base": "__simple_base",
        "path": "C:/txt/1.txt"
    },
    "specifications": {
        "base": "__simple_base",
        "path": "C:/DOC/Specifications"
    }
}
"""

SETTINGS_TEMPLATE_JSON = SETTINGS_TEMPLATE_JSON.replace(
    "C:/", (str(DIR_ENV) + "\\").replace("\\", "\\\\")
)

SETTINGS_TEMPLATE = json.loads(SETTINGS_TEMPLATE_JSON)
for name in ["tx", "optt", "abc"]:
    project = SETTINGS_TEMPLATE[name]["path"]
    default_version = SETTINGS_TEMPLATE["__radix_base"]["options"]["default_version"]
    base_version = SETTINGS_TEMPLATE[name]["base_version"]

    for version in [default_version] + [
        base_version.format(number=i) for i in range(1, 4)
    ]:
        for file_name in ["!!designer.cmd", "!!server.cmd", "!!server-postgres.cmd"]:
            d = DIR_ENV / project / version
            d.mkdir(parents=True, exist_ok=True)
            (d / file_name).touch(exist_ok=True)

PATH_TEST_SETTINGS: Path = DIR_ENV / "test-settings.json"
PATH_TEST_SETTINGS.write_text(SETTINGS_TEMPLATE_JSON, encoding="utf-8")

# NOTE: Установка переменной окружения до импорта модулей, который явно или не явно импортируют модуль settings.py
os.environ["PATH_SETTINGS"] = str(PATH_TEST_SETTINGS)

import go

from core.commands import (
    resolve_whats,
    resolve_version,
    get_similar_version_path,
    get_file_by_what,
)
from core import (
    UnknownWhatException,
    is_like_a_version,
    get_similar_value,
    is_like_a_short_version,
)

from core import commands
import settings

SETTINGS = go.SETTINGS


# NOTE: Для отладки
# print(json.dumps(SETTINGS, indent=4, default=repr))


class TestCommon(TestCase):
    def test_override_base(self):
        self.assertEqual(
            SETTINGS["manager"]["options"]["what"],
            go.AvailabilityEnum.OPTIONAL,
        )
        self.assertEqual(
            SETTINGS["file"]["options"]["what"],
            go.AvailabilityEnum.PROHIBITED,
        )
        self.assertEqual(
            SETTINGS["specifications"]["options"]["what"],
            go.AvailabilityEnum.PROHIBITED,
        )

    def test_is_like_a_version(self):
        self.assertTrue(is_like_a_version("trunk"))
        self.assertTrue(is_like_a_version("екгтл"))
        self.assertTrue(is_like_a_version("екг"))
        self.assertTrue(is_like_a_version("trunk-екгтл"))
        self.assertTrue(is_like_a_version("trunk,екгтл"))
        self.assertTrue(is_like_a_version("3.2.22-trunk"))
        self.assertTrue(is_like_a_version("3.2.22-екгтл"))
        self.assertTrue(is_like_a_version("3.2.22"))
        self.assertTrue(is_like_a_version("3.2.22.10"))
        self.assertTrue(is_like_a_version("22"))
        self.assertTrue(is_like_a_version("22,23,24"))
        self.assertTrue(is_like_a_version("22,23,trunk"))
        self.assertTrue(is_like_a_version("22,23,t"))
        self.assertTrue(is_like_a_version("22,23,екгтл"))
        self.assertTrue(is_like_a_version("22,23,е"))

    def test_get_similar_value(self):
        items = ["server", "designer", "explorer"]
        self.assertEqual(get_similar_value("server", items), "server")
        self.assertEqual(get_similar_value("ser", items), "server")
        self.assertEqual(get_similar_value("s", items), "server")

    def test_is_like_a_short_version(self):
        self.assertTrue(is_like_a_short_version("22"))
        self.assertFalse(is_like_a_short_version("3.2.22"))


class TestSettings(TestCase):
    def test_get_versions_by_path(self):
        path = settings.get_path_by_name("tx")
        self.assertEqual(
            sorted(settings.get_versions_by_path(path).keys()),
            sorted(["3.2.1", "3.2.2", "3.2.3", "trunk"]),
        )

        path = settings.get_path_by_name("optt")
        self.assertEqual(
            sorted(settings.get_versions_by_path(path).keys()),
            sorted(["2.1.1", "2.1.2", "2.1.3", "trunk"]),
        )

    def test_get_project(self):
        self.assertIsNotNone(settings.get_project("tx"))
        self.assertIsNotNone(settings.get_project("t"))
        self.assertIsNotNone(settings.get_project("еч"))
        self.assertIsNotNone(settings.get_project("е"))

        self.assertIsNotNone(settings.get_project("optt"))
        self.assertIsNotNone(settings.get_project("o"))
        self.assertIsNotNone(settings.get_project("op"))
        self.assertIsNotNone(settings.get_project("щзее"))
        self.assertIsNotNone(settings.get_project("щ"))
        self.assertIsNotNone(settings.get_project("щз"))

    def test_resolve_name(self):
        self.assertEqual(settings.resolve_name("t"), "tx")
        self.assertEqual(settings.resolve_name("tx"), "tx")
        self.assertEqual(settings.resolve_name("еч"), "tx")
        self.assertEqual(settings.resolve_name("щзе"), "optt")
        self.assertEqual(settings.resolve_name("o"), "optt")
        self.assertEqual(settings.resolve_name("optt"), "optt")

    def test_get_path_by_name(self):
        self.assertIsNotNone(settings.get_path_by_name("tx"))
        self.assertIsNotNone(settings.get_path_by_name("t"))
        self.assertIsNotNone(settings.get_path_by_name("еч"))
        self.assertIsNotNone(settings.get_path_by_name("е"))

        self.assertIsNotNone(settings.get_path_by_name("optt"))
        self.assertIsNotNone(settings.get_path_by_name("o"))
        self.assertIsNotNone(settings.get_path_by_name("op"))
        self.assertIsNotNone(settings.get_path_by_name("щзее"))
        self.assertIsNotNone(settings.get_path_by_name("щ"))
        self.assertIsNotNone(settings.get_path_by_name("щз"))


class TestCommands(TestCase):
    def test_resolve_whats(self):
        self.assertEqual(resolve_whats("tx", "designer"), ["designer"])
        self.assertEqual(resolve_whats("tx", "des"), ["designer"])
        self.assertEqual(resolve_whats("tx", "d"), ["designer"])
        self.assertEqual(resolve_whats("tx", "вуышптук"), ["designer"])
        self.assertEqual(resolve_whats("tx", "вуы"), ["designer"])
        self.assertEqual(resolve_whats("tx", "в"), ["designer"])

        self.assertEqual(resolve_whats("tx", "server"), ["server"])
        self.assertEqual(resolve_whats("tx", "ser"), ["server"])
        self.assertEqual(resolve_whats("tx", "s"), ["server"])
        self.assertEqual(resolve_whats("tx", "ыукмук"), ["server"])
        self.assertEqual(resolve_whats("tx", "ыук"), ["server"])
        self.assertEqual(resolve_whats("tx", "ы"), ["server"])

        self.assertEqual(resolve_whats("tx", "designer+server"), ["designer", "server"])
        self.assertEqual(resolve_whats("tx", "вуышптук+server"), ["designer", "server"])
        self.assertEqual(resolve_whats("tx", "вуышптук+ыукмук"), ["designer", "server"])
        self.assertEqual(resolve_whats("tx", "d+s"), ["designer", "server"])
        self.assertEqual(resolve_whats("tx", "в+ы"), ["designer", "server"])

        self.assertEqual(resolve_whats("manager", "up"), ["up"])
        self.assertEqual(resolve_whats("m", "up"), ["up"])
        self.assertEqual(resolve_whats("ь", "up"), ["up"])
        self.assertEqual(resolve_whats("ь", "гз"), ["up"])

        self.assertRaises(UnknownWhatException, resolve_whats, "tx", "BFG")

    def test_resolve_version(self):
        self.assertEqual(resolve_version("tx", "trunk"), "trunk")
        self.assertEqual(resolve_version("tx", "tr"), "trunk")
        self.assertEqual(resolve_version("еч", "trunk"), "trunk")
        self.assertEqual(resolve_version("optt", "trunk"), "trunk")
        self.assertEqual(resolve_version("щзе", "trunk"), "trunk")
        self.assertEqual(resolve_version("tx", "екгтл"), "trunk")
        self.assertEqual(resolve_version("tx", "ек"), "trunk")
        self.assertEqual(resolve_version("tx", "3.2.3"), "3.2.3")
        self.assertEqual(resolve_version("tx", "3"), "3.2.3")

    def test_get_similar_version_path(self):
        versions: dict = settings.get_project("tx")["versions"]
        path_tx_trunk: str = versions["trunk"]
        path_tx_3_2_3: str = versions["3.2.3"]

        self.assertEqual(get_similar_version_path("tx", "trunk"), path_tx_trunk)
        self.assertEqual(get_similar_version_path("tx", "t"), path_tx_trunk)
        self.assertEqual(get_similar_version_path("tx", "tru"), path_tx_trunk)
        self.assertEqual(get_similar_version_path("tx", "екгтл"), path_tx_trunk)
        self.assertEqual(get_similar_version_path("tx", "екг"), path_tx_trunk)
        self.assertEqual(get_similar_version_path("tx", "е"), path_tx_trunk)
        self.assertEqual(get_similar_version_path("еч", "trunk"), path_tx_trunk)
        self.assertEqual(get_similar_version_path("еч", "екгтл"), path_tx_trunk)
        self.assertEqual(get_similar_version_path("tx", "3.2.3"), path_tx_3_2_3)
        self.assertEqual(get_similar_version_path("tx", "3"), path_tx_3_2_3)

    def test_get_file_by_what(self):
        self.assertEqual(
            get_file_by_what("tx", "designer"),
            get_file_by_what("tx", "d"),
        )
        self.assertEqual(
            get_file_by_what("tx", "s"),
            get_file_by_what("tx", "ы"),
        )

        value_designer: str = get_file_by_what("tx", "designer")
        self.assertTrue(isinstance(value_designer, str))
        self.assertTrue(value_designer.endswith("!!designer.cmd"))

        value_server: dict = get_file_by_what("tx", "server")
        self.assertTrue(isinstance(value_server, dict))
        self.assertEqual(
            value_server,
            {
                "__default__": "ora",
                "ora": "!!server.cmd",
                "pg": "!!server-postgres.cmd",
            },
        )

        value_update: list = get_file_by_what("tx", "update")
        self.assertTrue(isinstance(value_update, list))
        self.assertEqual(value_update, ["svn update", commands.svn_update])


class TestGo(TestCase):
    def test_parse_cmd_args(self):
        self.assertEqual(
            go.parse_cmd_args("tx s".split()),
            [go.Command(name="tx", version=None, what="server", args=[])],
        )
        self.assertEqual(
            go.parse_cmd_args("abc 3 s".split()),
            [go.Command(name="abc", version="4.1.3.10-dev", what="server", args=[])],
        )

        self.assertEqual(
            go.parse_cmd_args("tx s pg".split()),
            [go.Command(name="tx", version=None, what="server", args=["pg"])],
        )

        self.assertEqual(
            go.parse_cmd_args("еч ы зп".split()),
            [go.Command(name="tx", version=None, what="server", args=["зп"])],
        )

        self.assertEqual(
            go.parse_cmd_args("tx 3 s".split()),
            [go.Command(name="tx", version="3.2.3", what="server", args=[])],
        )
        self.assertEqual(
            go.parse_cmd_args("tx 2-tr s".split()),
            [
                go.Command(name="tx", version="3.2.2", what="server", args=[]),
                go.Command(name="tx", version="3.2.3", what="server", args=[]),
                go.Command(name="tx", version="trunk", what="server", args=[]),
            ],
        )
        self.assertEqual(
            go.parse_cmd_args("tx 2,tr s".split()),
            [
                go.Command(name="tx", version="3.2.2", what="server", args=[]),
                go.Command(name="tx", version="trunk", what="server", args=[]),
            ],
        )

        self.assertEqual(
            go.parse_cmd_args("tx 3-tr d+s abc 123".split()),
            [
                go.Command(
                    name="tx", version="3.2.3", what="designer", args=["abc", "123"]
                ),
                go.Command(
                    name="tx", version="3.2.3", what="server", args=["abc", "123"]
                ),
                go.Command(
                    name="tx", version="trunk", what="designer", args=["abc", "123"]
                ),
                go.Command(
                    name="tx", version="trunk", what="server", args=["abc", "123"]
                ),
            ],
        )
