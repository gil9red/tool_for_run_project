#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
from datetime import date, timedelta

from core.svn import URL_DEFAULT_SVN_PATH, Revision, run_svn_command


TEXT_RELEASE_VERSION = "Release version "
PATTERN_RELEASE_VERSION = re.compile(rf"{TEXT_RELEASE_VERSION}([\d.]+) ")


def get_last_release_version(
    version: str,
    start_revision: str = "HEAD",
    last_days: int = 30,
    url_svn_path: str = URL_DEFAULT_SVN_PATH,
) -> str:
    url = f"{url_svn_path}/{version}"

    end_date = date.today() - timedelta(days=last_days)

    revisions: list[Revision] = run_svn_command(
        [
            "log",
            "--xml",
            "--search",
            TEXT_RELEASE_VERSION,
            "--revision",
            # Если в паре значений первым идет большее значение, то поиск будет идти от большего к меньшему
            f"{start_revision}:{{{end_date}}}",
        ],
        url_or_path=url,
    )

    for r in revisions:
        m = PATTERN_RELEASE_VERSION.search(r.msg)
        if not m:
            raise Exception(f"Не удалось вытащить версию релиза из {r.msg!r}")

        return m.group(1)

    raise Exception("Не удалось найти ревизию!")


if __name__ == "__main__":
    print(get_last_release_version(version="trunk", last_days=60))
    print(get_last_release_version(version="3.2.48.10"))
    print(get_last_release_version(version="3.2.47.10"))
    # 3.2.48.10
    # 3.2.48.10.6
    # 3.2.47.10.23
