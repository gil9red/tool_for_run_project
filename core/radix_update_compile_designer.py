#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import os
import subprocess

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Callable
from timeit import default_timer

from core import run_file


@dataclass
class SvnUpResult:
    is_success: bool = False
    has_conflicts: bool = False
    is_about_cleanup: bool = False


@contextmanager
def console_print_header(title: str):
    start_time: float = default_timer()

    print()
    print("-" * 100)
    print(f'Start "{title}"')
    try:
        yield
    finally:
        seconds = int(default_timer() - start_time)
        print(f'Finish "{title}". Elapsed time: {timedelta(seconds=seconds)}')
        print("-" * 100)


def execute(
    command: str | list[str],
    directory: Path | str | None = None,
    encoding: str = "utf-8",
    on_out_line_func: Callable[[str], None] = print,
    assert_return_code: bool = True,
):
    print(
        f"[execute] command={command!r}, directory={str(directory)!r}, encoding={encoding!r}"
    )

    popen = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding=encoding,
        cwd=directory,
        shell=True,
    )
    for stdout_line in iter(popen.stdout.readline, ""):
        on_out_line_func(stdout_line)
    popen.stdout.close()
    return_code = popen.wait()
    if return_code and assert_return_code:
        raise subprocess.CalledProcessError(return_code, command)


def execute_svn_up(
    path: Path | str,
    on_out_line_func: Callable[[str], None] = print,
) -> SvnUpResult:
    result: SvnUpResult = SvnUpResult()

    def _fill_result_on_out_line_func(line: str):
        on_out_line_func(line)

        # TODO:
        # line_lower: str | bytes = line.lower()
        # if isinstance(line_lower, bytes):
        #     try:
        #         line_lower: str = str(line_lower, encoding="utf-8")
        #     except UnicodeError: # TODO: Или
        #         line_lower: str = str(line_lower, encoding="latin-1")
        #
        # print(line_lower)

        # TODO: Мб тут в байтах учитывать значения?
        line_lower: str = line.lower()

        if "at revision" in line_lower or "updated to revision" in line_lower:
            result.is_success = True

        if "summary of conflicts:" in line_lower:
            result.has_conflicts = True

        if "cleanup" in line_lower:
            result.is_about_cleanup = True

    execute(
        "svn up . --non-interactive",
        directory=path,
        on_out_line_func=_fill_result_on_out_line_func,
        encoding="latin-1",  # TODO: Проверить, с utf-8 была ошибка
        assert_return_code=False,
    )

    if result.has_conflicts:
        # NOTE: Успешность скачивания, конфликты отдельно и могут по свойствам типа svn:ignore
        result.is_success = False

    return result


def run(path: Path | str):
    print(path)

    start_time_ms: float = default_timer()

    with console_print_header("SVN UP"):
        result_svn_up: SvnUpResult = execute_svn_up(
            path=path,
            on_out_line_func=lambda line: print("[1]", line, end=""),
        )
        # TODO: Для отладки может понадобиться
        print("result_svn_up:", result_svn_up)

        if not result_svn_up.is_success:
            if result_svn_up.is_about_cleanup:
                execute(
                    "svn cleanup .",
                    directory=path,
                    on_out_line_func=lambda line: print("[1.1]", line, end=""),
                )

                lines: list[str] = []

                def _on_out_line_func(line: str):
                    print("[1.2]", line, end="")
                    lines.append(line)

                result_svn_up: SvnUpResult = execute_svn_up(
                    path=path,
                    on_out_line_func=_on_out_line_func,
                )

                if not result_svn_up.is_success:
                    raise Exception("".join(lines))
            else:
                raise Exception("Error")  # TODO:

    with console_print_header("BUILD-KERNEL"):
        execute(
            "call ant clean -f build-kernel.xml & call ant distributive -f build-kernel.xml",
            directory=path,
            on_out_line_func=lambda line: print("[2]", line, end=""),
        )

    with console_print_header("BUILD-ADS"):
        execute(
            "call ant -f build-ads.xml",
            directory=path,
            on_out_line_func=lambda line: print("[3]", line, end=""),
        )

    with console_print_header("DESIGNER"):
        file_name = path / "!!designer.cmd"
        run_file(file_name)

    print(f"\nTotal elapsed: {timedelta(seconds=int(default_timer() - start_time_ms))}")


if __name__ == "__main__":
    import sys

    # # TODO:
    path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    # # # TODO:
    # # path = r"C:\DEV__TX\3.2.41.10"
    # # path = r"C:\DEV__TX\3.2.43.10"
    # # path = r"C:\DEV__TX\3.2.44.10"
    # # path = r"C:\DEV__OPTT"
    # # path = r"C:\DEV__OPTT\2.1.14.1"
    # # path = r"C:\DEV__OPTT\2.1.16.1"
    # # path = r"C:\DEV__OPTT\2.1.15.1"
    path = Path(path)
    run(path)
