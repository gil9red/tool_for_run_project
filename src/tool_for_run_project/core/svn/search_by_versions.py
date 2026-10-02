#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
from collections import defaultdict
from datetime import date, timedelta

from tool_for_run_project.core.svn import (
    URL_DEFAULT_SVN_PATH,
    Revision,
    run_svn_command,
)

PATTERN_VERSION: re.Pattern[str] = re.compile(r"/dev/(.+?)/")


def search(
    text: str,
    last_days: int = 30,
    url_svn_path: str = URL_DEFAULT_SVN_PATH,
    return_revisions: bool = False,
) -> list[str] | dict[str, list[Revision]]:
    start_date = date.today() - timedelta(days=last_days)

    versions: list[str] = []
    version_by_revisions: dict[str, list[Revision]] = defaultdict(list)

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

                if return_revisions:
                    if r not in version_by_revisions.get(version, []):
                        version_by_revisions[version].append(r)
                else:
                    if version not in versions:
                        versions.append(version)

    return version_by_revisions if return_revisions else versions


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
