#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import subprocess
import xml.etree.ElementTree as ET

from dataclasses import dataclass, field
from datetime import datetime
from xml.etree.ElementTree import Element


URL_DEFAULT_SVN_PATH: str = "svn+cplus://svn2.compassplus.ru/twrbs/trunk/dev"


@dataclass
class RevisionPath:
    prop_mods: bool
    text_mods: bool
    kind: str
    action: str
    path: str

    @classmethod
    def parse_from(cls, el: Element) -> "RevisionPath":
        return cls(
            prop_mods=el.attrib["prop-mods"] == "true",
            text_mods=el.attrib["text-mods"] == "true",
            kind=el.attrib["kind"],
            action=el.attrib["action"],
            path=el.text,
        )


@dataclass
class Revision:
    number: int
    author: str
    date: datetime
    msg: str
    paths: list[RevisionPath] = field(default_factory=list)

    @classmethod
    def parse_from(cls, el: Element) -> "Revision":
        return cls(
            number=int(el.attrib["revision"]),
            author=el.find("author").text,
            date=datetime.strptime(el.find("date").text, "%Y-%m-%dT%H:%M:%S.%f%z"),
            msg=el.find("msg").text,
            paths=[
                RevisionPath.parse_from(el_path)
                for el_path in el.findall("./paths/path")
            ],
        )


def run_svn_command(
    args: list[str],
    url_or_path: str = URL_DEFAULT_SVN_PATH,
) -> list[Revision]:
    args.insert(0, "svn")
    args.append(url_or_path)

    data: bytes = subprocess.check_output(args)
    root = ET.fromstring(data)
    return [
        Revision.parse_from(logentry_el) for logentry_el in root.findall(".//logentry")
    ]


if __name__ == "__main__":
    path_dir = f"{URL_DEFAULT_SVN_PATH}/trunk"

    revisions: list[Revision] = run_svn_command(
        ["log", "--xml", "--limit", "3"],
        url_or_path=path_dir,
    )
    print(f"Revisions ({len(revisions)}):")
    for r in revisions:
        print(r)

    print("\n" + "-" * 10 + "\n")

    revisions: list[Revision] = run_svn_command(
        ["log", "--verbose", "--xml", "--limit", "3"],
        url_or_path=path_dir,
    )
    print(f"Revisions ({len(revisions)}):")
    for r in revisions:
        print(r)
        for p in r.paths:
            print(f"    {p}")
