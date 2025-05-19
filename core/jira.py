#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import sys
import os
import webbrowser


JIRA_HOST: str | None = os.getenv("JIRA_HOST")
if not JIRA_HOST:
    raise Exception("JIRA_HOST environment variable is not set!")


if len(sys.argv) == 1:
    print("Example: jira TXI-926")
    print("Example: jira TXI-926 TXI-927 TXI-928")
    sys.exit()

for number in sys.argv[1:]:
    number = number.strip()

    url = f"{JIRA_HOST}/browse/{number}"
    print(f"Open url: {url}")

    webbrowser.open(url)
