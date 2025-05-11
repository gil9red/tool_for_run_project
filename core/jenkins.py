#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from datetime import datetime

import requests

from core import GoException


class JenkinsJobCheckException(GoException):
    pass


def do_check_jenkins_job(url: str, version: str):
    url = url.format(version=version)

    rs = requests.get(url)
    if rs.status_code == 404:
        print(f"[!] Сборки для версии {version} нет.")
        return

    rs.raise_for_status()

    data = rs.json()

    # "0:39:56.476184" -> "0:39:56"
    duration = datetime.now() - datetime.fromtimestamp(data["timestamp"] / 1000)
    duration_str = str(duration).split(".")[0]

    result = data["result"]
    if not result:
        raise JenkinsJobCheckException(
            f"Сборка еще в процессе, прошло {duration_str}.\nCсылка: {data['url']}"
        )

    if result != "SUCCESS":
        raise JenkinsJobCheckException(
            f"Сборка поломанная, обновление прервано. "
            f"С последнего запуска прошло {duration_str}.\nCсылка: {data['url']}"
        )
