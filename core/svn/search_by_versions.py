#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
from datetime import date, timedelta

from core.svn import URL_DEFAULT_SVN_PATH, run_svn_command


PATTERN_VERSION = re.compile(r"/dev/(.+?)/")


def search(
    text: str,
    last_days: int = 30,
    url_svn_path: str = URL_DEFAULT_SVN_PATH,
) -> list[str]:
    start_date = date.today() - timedelta(days=last_days)

    versions: list[str] = []
    for r in run_svn_command(
        [
            "log",
            "--verbose",
            "--xml",
            "--search",
            text,
            "--revision",
            # Порядок имеет значение - выдача ревизий тут будет от меньшей к большей
            f"{{{start_date}}}:HEAD",
        ],
        url_or_path=url_svn_path,
    ):
        for path in r.paths:
            if m := PATTERN_VERSION.search(path.path):
                version = m.group(1)
                if version not in versions:
                    versions.append(version)

    return versions


if __name__ == "__main__":
    versions: list[str] = search(text="ipetrash")
    print(versions)
    # ['trunk', '3.2.36.10', '3.2.35.10']

    versions: list[str] = search(
        text="ipetrash",
        last_days=365,
        url_svn_path="svn+cplus://svn2.compassplus.ru/twrbs/csm/optt",
    )
    print(versions)
    # ['trunk', '2.1.12.1']
