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
            "action": "${AvailabilityEnum.REQUIRED}",
            "args": "${AvailabilityEnum.OPTIONAL}",
            "default_version": "trunk"
        },
        "actions": {
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
        "path": [
            "C:/DEV__ABC",
            "C:/local/remote/foo/bar",
            "C:/local/remote/foo/abc"
        ],
        "base_version": "4.1.{number}.10-dev",
        "jenkins_url": "${self['abc']['vars']['URL_JENKINS'] + '/job/ABC_{version}_build/lastBuild/api/json?tree=result,timestamp,url'}",
        "svn_dev_url": "svn://127.0.0.1/abc/dev/trunk"
    },
    "__simple_base": {
        "options": {
            "version": "${AvailabilityEnum.PROHIBITED}",
            "action": "${AvailabilityEnum.PROHIBITED}",
            "args": "${AvailabilityEnum.PROHIBITED}"
        }
    },
    "manager": {
        "base": "__simple_base",
        "path": "C:/DEV__RADIX/manager/manager/bin/manager.cmd",
        "options": {
            "action": "${AvailabilityEnum.OPTIONAL}"
        },
        "actions": {
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
    path_value: str | list[str] = SETTINGS_TEMPLATE[name]["path"]
    default_version = SETTINGS_TEMPLATE["__radix_base"]["options"]["default_version"]
    base_version = SETTINGS_TEMPLATE[name]["base_version"]

    def _create_files(path: str, version: str):
        for file_name in ["!!designer.cmd", "!!server.cmd", "!!server-postgres.cmd"]:
            d = DIR_ENV / path / version
            d.mkdir(parents=True, exist_ok=True)
            (d / file_name).touch(exist_ok=True)

    if isinstance(path_value, str):
        path: str = path_value
        for version_name in [default_version] + [
            base_version.format(number=i) for i in [1, 2, 3]
        ]:
            _create_files(path, version_name)
    else:
        version = 1
        for path in path_value:
            for i in range(3):
                _create_files(path, base_version.format(number=version))
                version += 1

PATH_TEST_SETTINGS: Path = DIR_ENV / "test-settings.json"
PATH_TEST_SETTINGS.write_text(SETTINGS_TEMPLATE_JSON, encoding="utf-8")

# NOTE: Установка переменной окружения до импорта модулей, который явно или не явно импортируют модуль settings.py
os.environ["PATH_SETTINGS"] = str(PATH_TEST_SETTINGS)

import go

from core.commands import (
    resolve_actions,
    resolve_version,
    get_similar_version_path,
    get_file_by_action,
)
from core import (
    UnknownActionException,
    UnknownArgException,
    UnknownNameException,
    UnknownVersionException,
    MultipleResultsFoundError,
    resolve_alias,
    is_like_a_version,
    get_similar_value,
    is_like_a_short_version,
)

from core import commands
import settings

SETTINGS = go.SETTINGS


# NOTE: Для отладки
# print(json.dumps(SETTINGS, indent=4, default=repr))
# quit()


class TestCommon(TestCase):
    def test_override_base(self):
        self.assertEqual(
            SETTINGS["manager"]["options"]["action"],
            go.AvailabilityEnum.OPTIONAL,
        )
        self.assertEqual(
            SETTINGS["file"]["options"]["action"],
            go.AvailabilityEnum.PROHIBITED,
        )
        self.assertEqual(
            SETTINGS["specifications"]["options"]["action"],
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
        with self.subTest(msg="OK"):
            items = ["server", "designer", "explorer"]
            self.assertEqual(get_similar_value("server", items), "server")
            self.assertEqual(get_similar_value("ser", items), "server")
            self.assertEqual(get_similar_value("s", items), "server")

        with self.subTest(msg="Not found"):
            self.assertIsNone(get_similar_value("server", []))

            items = ["server", "designer", "explorer"]
            self.assertIsNone(get_similar_value("erver", items))
            self.assertIsNone(get_similar_value("!server", items))
            self.assertIsNone(get_similar_value("document", items))

        with self.subTest(msg="Multiple results found error"):
            items = ["revert", "run", "run2", "run3"]

            with self.assertRaises(MultipleResultsFoundError) as cm:
                get_similar_value("r", items)
            self.assertEqual(["revert", "run", "run2", "run3"], cm.exception.variants)

            with self.assertRaises(MultipleResultsFoundError) as cm:
                self.assertIsNone(get_similar_value("ru", items))
            self.assertEqual(["run", "run2", "run3"], cm.exception.variants)

    def test_is_like_a_short_version(self):
        self.assertTrue(is_like_a_short_version("22"))
        self.assertFalse(is_like_a_short_version("3.2.22"))


class TestSettings(TestCase):
    def test_get_versions_by_path(self):
        path_value: str | list[str] = settings.get_path_by_name("tx")
        self.assertTrue(isinstance(path_value, str))
        self.assertEqual(
            sorted(settings.get_versions_by_path(path_value).keys()),
            sorted(["3.2.1", "3.2.2", "3.2.3", "trunk"]),
        )

        path_value: str | list[str] = settings.get_path_by_name("optt")
        self.assertTrue(isinstance(path_value, str))
        self.assertEqual(
            sorted(settings.get_versions_by_path(path_value).keys()),
            sorted(["2.1.1", "2.1.2", "2.1.3", "trunk"]),
        )

        path_value: str | list[str] = settings.get_path_by_name("abc")
        self.assertTrue(isinstance(path_value, list))

        version_by_path: dict[str, str] = dict()
        for path in path_value:
            version_by_path.update(settings.get_versions_by_path(path))
        self.assertEqual(
            sorted(version_by_path.keys()),
            sorted(
                [
                    "4.1.1.10-dev",
                    "4.1.2.10-dev",
                    "4.1.3.10-dev",
                    "4.1.4.10-dev",
                    "4.1.5.10-dev",
                    "4.1.6.10-dev",
                    "4.1.7.10-dev",
                    "4.1.8.10-dev",
                    "4.1.9.10-dev",
                ]
            ),
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

        with self.assertRaises(UnknownNameException):
            settings.resolve_name("1212")

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

        self.assertIsNotNone(settings.get_path_by_name("abc"))
        self.assertIsNotNone(settings.get_path_by_name("a"))
        self.assertIsNotNone(settings.get_path_by_name("фис"))


class TestCommands(TestCase):
    def test_resolve_actions(self):
        self.assertEqual(resolve_actions("tx", "designer"), ["designer"])
        self.assertEqual(resolve_actions("tx", "des"), ["designer"])
        self.assertEqual(resolve_actions("tx", "d"), ["designer"])
        self.assertEqual(resolve_actions("tx", "вуышптук"), ["designer"])
        self.assertEqual(resolve_actions("tx", "вуы"), ["designer"])
        self.assertEqual(resolve_actions("tx", "в"), ["designer"])

        self.assertEqual(resolve_actions("tx", "server"), ["server"])
        self.assertEqual(resolve_actions("tx", "ser"), ["server"])
        self.assertEqual(resolve_actions("tx", "s"), ["server"])
        self.assertEqual(resolve_actions("tx", "ыукмук"), ["server"])
        self.assertEqual(resolve_actions("tx", "ыук"), ["server"])
        self.assertEqual(resolve_actions("tx", "ы"), ["server"])

        self.assertEqual(
            resolve_actions("tx", "designer+server"), ["designer", "server"]
        )
        self.assertEqual(
            resolve_actions("tx", "вуышптук+server"), ["designer", "server"]
        )
        self.assertEqual(
            resolve_actions("tx", "вуышптук+ыукмук"), ["designer", "server"]
        )
        self.assertEqual(resolve_actions("tx", "d+s"), ["designer", "server"])
        self.assertEqual(resolve_actions("tx", "в+ы"), ["designer", "server"])

        self.assertEqual(resolve_actions("manager", "up"), ["up"])
        self.assertEqual(resolve_actions("m", "up"), ["up"])
        self.assertEqual(resolve_actions("ь", "up"), ["up"])
        self.assertEqual(resolve_actions("ь", "гз"), ["up"])

        with self.assertRaises(UnknownActionException):
            resolve_actions("tx", "1212")

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

        with self.assertRaises(UnknownVersionException):
            resolve_version("tx", "foobar")

    def test_resolve_alias(self):
        supported: list[str] = [
            "server",
            "explorer",
            "designer",
            "designer2",
            "manager",
        ]
        for expected, alias in [
            ("server", "SERVER"),
            ("server", "server"),
            ("server", "ser"),
            ("server", "s"),
            ("server", "ЫУКМУК"),
            ("server", "ыукмук"),
            ("server", "ыук"),
            ("server", "ы"),
            # NOTE: Те же проверки, что и для server
            ("explorer", "EXPLORER"),
            ("explorer", "explorer"),
            ("explorer", "exp"),
            ("explorer", "e"),
            ("explorer", "УЧЗДЩКУК"),
            ("explorer", "учздщкук"),
            ("explorer", "учз"),
            ("explorer", "у"),
            # NOTE: Часть проверок общая, остальные для совпадений имен
            ("designer", "DESIGNER"),
            ("designer", "designer"),
            ("designer", "вуышптук"),
            ("designer2", "DESIGNER2"),
            ("designer2", "designer2"),
            ("designer2", "вуышптук2"),
            # NOTE: Тут будет ошибка из-за совпадения начальных символов
            #       Непонятно, "des" относится к "designer" или к "designer2"
            (MultipleResultsFoundError, "DES"),
            (MultipleResultsFoundError, "des"),
            (MultipleResultsFoundError, "d"),
            (MultipleResultsFoundError, "ВУЫ"),
            (MultipleResultsFoundError, "вуы"),
            (MultipleResultsFoundError, "в"),
            # NOTE: Просто невалидные значения
            (UnknownActionException, "1212"),
            (UnknownActionException, "NONE"),
            (UnknownActionException, "None"),
            (UnknownActionException, ""),
        ]:
            with self.subTest(expected=expected, alias=alias, supported=supported):
                if isinstance(expected, str):
                    self.assertEqual(
                        expected,
                        resolve_alias(
                            alias=alias,
                            supported=supported,
                            unknown_alias_exception_cls=UnknownActionException,
                        ),
                    )
                else:
                    with self.assertRaises(expected):
                        resolve_alias(
                            alias=alias,
                            supported=supported,
                            unknown_alias_exception_cls=expected,
                        )

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

        # Версии в разных папках
        self.assertIn("DEV__ABC", get_similar_version_path("abc", "1"))
        self.assertIn(r"local\remote\foo\bar", get_similar_version_path("abc", "4"))
        self.assertIn(r"local\remote\foo\abc", get_similar_version_path("abc", "7"))

    def test_get_file_by_action(self):
        self.assertEqual(
            get_file_by_action("tx", "designer"),
            get_file_by_action("tx", "d"),
        )
        self.assertEqual(
            get_file_by_action("tx", "s"),
            get_file_by_action("tx", "ы"),
        )

        value_designer: str = get_file_by_action("tx", "designer")
        self.assertTrue(isinstance(value_designer, str))
        self.assertTrue(value_designer.endswith("!!designer.cmd"))

        value_server: dict = get_file_by_action("tx", "server")
        self.assertTrue(isinstance(value_server, dict))
        self.assertEqual(
            value_server,
            {
                "__default__": "ora",
                "ora": "!!server.cmd",
                "pg": "!!server-postgres.cmd",
            },
        )

        value_update: list = get_file_by_action("tx", "update")
        self.assertTrue(isinstance(value_update, list))
        self.assertEqual(value_update, ["svn update", commands.svn_update])


class TestGo(TestCase):
    def test_parse_cmd_args(self):
        self.assertEqual(
            go.parse_cmd_args("tx s".split()),
            [go.Command(name="tx", version="trunk", action="server", args=["ora"])],
        )
        self.assertEqual(
            go.parse_cmd_args("abc 3 s".split()),
            [
                go.Command(
                    name="abc", version="4.1.3.10-dev", action="server", args=["ora"]
                )
            ],
        )

        self.assertEqual(
            go.parse_cmd_args("tx s pg".split()),
            [go.Command(name="tx", version="trunk", action="server", args=["pg"])],
        )

        self.assertEqual(
            go.parse_cmd_args("еч ы зп".split()),
            [go.Command(name="tx", version="trunk", action="server", args=["pg"])],
        )

        self.assertEqual(
            go.parse_cmd_args("tx 3 s".split()),
            [go.Command(name="tx", version="3.2.3", action="server", args=["ora"])],
        )
        self.assertEqual(
            go.parse_cmd_args("tx 2-tr s".split()),
            [
                go.Command(name="tx", version="3.2.2", action="server", args=["ora"]),
                go.Command(name="tx", version="3.2.3", action="server", args=["ora"]),
                go.Command(name="tx", version="trunk", action="server", args=["ora"]),
            ],
        )
        self.assertEqual(
            go.parse_cmd_args("tx 2,tr s".split()),
            [
                go.Command(name="tx", version="3.2.2", action="server", args=["ora"]),
                go.Command(name="tx", version="trunk", action="server", args=["ora"]),
            ],
        )

        with self.assertRaises(UnknownArgException):
            go.parse_cmd_args("tx 3-tr d+s abc 123".split())

        self.assertEqual(
            go.parse_cmd_args("tx 3-tr d+s зп 123".split()),
            [
                go.Command(
                    name="tx", version="3.2.3", action="designer", args=["зп", "123"]
                ),
                go.Command(
                    name="tx", version="3.2.3", action="server", args=["pg", "123"]
                ),
                go.Command(
                    name="tx", version="trunk", action="designer", args=["зп", "123"]
                ),
                go.Command(
                    name="tx", version="trunk", action="server", args=["pg", "123"]
                ),
            ],
        )

        self.assertEqual(
            go.parse_cmd_args("tx 3-tr d+s".split()),
            [
                go.Command(name="tx", version="3.2.3", action="designer", args=[]),
                go.Command(name="tx", version="3.2.3", action="server", args=["ora"]),
                go.Command(name="tx", version="trunk", action="designer", args=[]),
                go.Command(name="tx", version="trunk", action="server", args=["ora"]),
            ],
        )

        self.assertEqual(
            go.parse_cmd_args("t д release version".split()),
            [
                go.Command(
                    name="tx",
                    version="trunk",
                    action="log",
                    args=["release", "version"],
                )
            ],
        )
