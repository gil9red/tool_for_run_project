#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from pathlib import Path
from psutil import process_iter, Process, Error, NoSuchProcess, AccessDenied


def is_server(p: Process) -> bool:
    try:
        return "org.radixware.kernel.server.Server" in p.cmdline()
    except AccessDenied as e:
        print(f"Access denied: {e}")
        return False
    except NoSuchProcess:
        return False


def is_explorer(p: Process) -> bool:
    try:
        return "org.radixware.kernel.explorer.Explorer" in p.cmdline()
    except AccessDenied as e:
        print(f"Access denied: {e}")
        return False
    except NoSuchProcess:
        return False


def is_designer(p: Process) -> bool:
    try:
        return p.name().startswith("designer")
    except AccessDenied as e:
        print(f"Access denied: {e}")
        return False
    except NoSuchProcess:
        return False


def is_found(p: Process, cwd: str | Path = None) -> bool:
    if isinstance(cwd, str):
        cwd = Path(cwd)
    if cwd:
        is_equal_path = cwd.exists() and Path(p.cwd()).is_relative_to(cwd)
    else:
        is_equal_path = True

    return ("java" in p.name() or is_designer(p)) and is_equal_path


def get_processes(cwd: str | Path = None) -> list[Process]:
    items = []
    for p in process_iter():
        try:
            if is_found(p, cwd):
                items.append(p)
        except Error:
            pass
    return items


def kill_servers(cwd: str | Path = None) -> list[int]:
    pids = []

    for p in get_processes(cwd):
        if is_server(p):
            print(f"Kill server #{p.pid}")
            pids.append(p.pid)
            p.kill()

    return pids


def kill_explorers(cwd: str | Path = None) -> list[int]:
    pids = []

    for p in get_processes(cwd):
        if is_explorer(p):
            print(f"Kill explorer #{p.pid}")
            pids.append(p.pid)
            p.kill()

    return pids


def kill_designers(cwd: str | Path = None) -> list[int]:
    pids = []

    for p in get_processes(cwd):
        if is_designer(p):
            print(f"Kill designer #{p.pid}")
            pids.append(p.pid)
            p.kill()

    return pids


if __name__ == "__main__":
    kill_servers()
    kill_explorers()
    kill_designers()
