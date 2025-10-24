#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
from datetime import date, timedelta

from core.svn import URL_DEFAULT_SVN_PATH, Revision, run_svn_command
from core.svn.get_last_release_version import get_last_release_version


def find_release_version(
    text: str,
    version: str,
    last_days: int = 30,
    url_svn_path: str = URL_DEFAULT_SVN_PATH,
) -> str:
    url = f"{url_svn_path}/{version}"

    end_date = date.today() - timedelta(days=last_days)

    revisions: list[Revision] = run_svn_command(
        [
            "log",
            # "--verbose",
            "--xml",
            "--search",
            text,
            "--revision",
            # Если в паре значений первым идет большее значение, то поиск будет идти от большего к меньшему
            f"HEAD:{{{end_date}}}",
        ],
        url_or_path=url,
    )
    if not revisions:
        raise Exception("Не удалось найти ревизию!")

    last_release_version: str = get_last_release_version(
        version=version,
        start_revision=str(revisions[0].number),
        last_days=last_days,
        url_svn_path=url_svn_path,
    )

    # Первый коммит, который искали попал уже в следующую версию, поэтому
    # нужно добавить 1 к последней версии:
    #     3.2.35.10.10 -> 3.2.35.10.11
    return re.sub(
        r"\.(\d+)$",  # Последнее число в версии
        lambda m: f".{int(m.group(1)) + 1}",  # Увеличение числа на 1
        last_release_version,
    )


if __name__ == "__main__":
    text = "ipetrash"
    print(find_release_version(text=text, version="3.2.48.10"))
    # 3.2.48.10.7

    print(find_release_version(text=text, version="3.2.47.10"))
    # 3.2.47.10.24
