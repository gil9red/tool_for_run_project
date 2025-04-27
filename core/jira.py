#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import sys
import webbrowser

from config import JIRA_HOST


if len(sys.argv) == 1:
    print("Example: jira TXI-926")
    print("Example: jira TXI-926 TXI-927 TXI-928")
    sys.exit()

for number in sys.argv[1:]:
    number = number.strip()

    url = f"{JIRA_HOST}/browse/{number}"
    print(f"Open url: {url}")

    webbrowser.open(url)
