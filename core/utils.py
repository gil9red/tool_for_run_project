#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import subprocess
import platform


def run_command_in_new_terminal(args: list[str]):
    if platform.system() == "Windows":
        subprocess.Popen(
            ["start", "cmd", "/k", *args], shell=True
        )
    elif platform.system() == "Linux":  # TODO: Не проверял
        subprocess.Popen(
            [
                "gnome-terminal",
                "--",
                "/bin/bash",
                "-c",
                f"{' '.join(args)}; exec bash",
            ]
        )
    elif platform.system() == "Darwin":  # macOS # TODO: Не проверял
        subprocess.Popen(
            [
                "osascript",
                "-e",
                f'''tell application "Terminal" to do script "{' '.join(args)}"''',
            ]
        )
    else:
        raise NotImplementedError("Unsupported operating system for launching in a new terminal.")


if __name__ == '__main__':
    import sys

    args = [sys.executable, "-c", "import uuid;print(uuid.uuid4())"]
    run_command_in_new_terminal(args=args)
