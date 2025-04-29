#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from go import from_ghbdtn
from core.commands import resolve_whats, resolve_version, get_similar_version_path
from core import is_like_a_version
from settings import SETTINGS, resolve_name


# TODO: unittest


for k in SETTINGS:
    assert resolve_name(k) == k
    assert resolve_name(from_ghbdtn(k)) == k
assert resolve_name("t") == "tx"
assert resolve_name("tx") == "tx"
assert resolve_name("еч") == "tx"
assert resolve_name("щзе") == "optt"
assert resolve_name("o") == "optt"
assert resolve_name("optt") == "optt"


resolve_what = lambda alias: resolve_whats("tx", alias)[0]

for k in SETTINGS["tx"]["whats"]:
    assert resolve_what(k) == k
    assert resolve_what(from_ghbdtn(k)) == k
assert resolve_what("d") == "designer"
assert resolve_what("в") == "designer"
assert resolve_what("вуы") == "designer"
assert resolve_what("e") == "explorer"
assert resolve_what("b") == "build"

# TODO: Зависит от окружения - без папок локально не работает
assert resolve_version("tx", "trunk") == "trunk"
assert resolve_version("tx", "tr") == "trunk"
assert resolve_version("еч", "trunk") == "trunk"
assert resolve_version("optt", "trunk") == "trunk"
assert resolve_version("щзе", "trunk") == "trunk"
assert resolve_version("tx", "екгтл") == "trunk"
assert resolve_version("tx", "ек") == "trunk"

# TODO: Зависит от окружения - без папок локально не работает
assert get_similar_version_path("tx", "trunk")
assert get_similar_version_path("tx", "tru")
assert get_similar_version_path("tx", "екгтл")
assert get_similar_version_path("tx", "екг")
assert get_similar_version_path("еч", "trunk")
assert get_similar_version_path("еч", "екгтл")

assert is_like_a_version("trunk")
assert is_like_a_version("екгтл")
assert is_like_a_version("екг")
assert is_like_a_version("trunk-екгтл")
assert is_like_a_version("trunk,екгтл")
assert is_like_a_version("3.2.22-trunk")
assert is_like_a_version("3.2.22-екгтл")
assert is_like_a_version("3.2.22")
assert is_like_a_version("3.2.22.10")
