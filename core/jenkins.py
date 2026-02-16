#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from datetime import datetime
from typing import Any

import requests

from core import GoException


class JenkinsJobCheckException(GoException):
    pass


# NOTE: InsecureRequestWarning: Unverified HTTPS request is being made to host 'jenkins-apd.compassplus.com'. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
#       Еще нужно в запросы добавлять verify=False
#       Так проще, чем таскать с собой сертификат, или обязывать указывать его
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)


def do_check_jenkins_job(url: str, version: str):
    url: str = url.format(version=version)

    rs = requests.get(url, verify=False)
    if rs.status_code == 404:
        print(f"[!] Сборки для версии {version} нет.")
        return

    rs.raise_for_status()

    data: dict[str, Any] = rs.json()

    # "0:39:56.476184" -> "0:39:56"
    duration = datetime.now() - datetime.fromtimestamp(data["timestamp"] / 1000)
    duration_str = str(duration).split(".")[0]

    result: str = data["result"]
    if not result:
        raise JenkinsJobCheckException(
            f"Сборка еще в процессе, прошло {duration_str}.\nCсылка: {data['url']}"
        )

    if result != "SUCCESS":
        raise JenkinsJobCheckException(
            f"Сборка поломанная, обновление прервано. "
            f"С последнего запуска прошло {duration_str}.\nCсылка: {data['url']}"
        )


if __name__ == "__main__":
    from settings import get_project, run_settings_preprocess

    run_settings_preprocess()

    settings = get_project("optt")
    jenkins_url: str = settings.get("jenkins_url")
    do_check_jenkins_job(jenkins_url, "trunk")
