#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from datetime import datetime

from core.svn import URL_DEFAULT_SVN_PATH, Revision, run_svn_command
from third_party.get_human_delta import get_human_delta


def get_age(
    version: str,
    url_svn_path: str = URL_DEFAULT_SVN_PATH,
) -> str:
    url = f"{url_svn_path}/{version}"

    revisions: list[Revision] = run_svn_command(
        ["log", "--xml", "-r", "1:HEAD", "--limit=1"],
        url_or_path=url,
    )
    if not revisions:
        raise Exception("Не удалось найти ревизию!")

    revision = revisions[0]

    delta = datetime.utcnow().replace(tzinfo=None) - revision.date.replace(tzinfo=None)

    lines = [
        f"Age: {get_human_delta(delta)}",
        "",
        f"First revision {revision.number}, author {revision.author}",
        f"    Date: {revision.date.isoformat(sep=' ', timespec='seconds')}",
        f"    Message: {revision.msg!r}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(get_age(version="3.2.35.10"))
    """
    Age: 839 days, 22:02:02

    First revision 305785, author ipetrash
        Date: 2023-07-05 13:22:37+00:00
        Message: 'Release version 3.2.35.10 (release based on revision 305756)'
    """

    print("\n" + "-" * 10 + "\n")

    print(get_age(version="3.2.48.10"))
