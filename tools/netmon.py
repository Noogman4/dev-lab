#!/usr/bin/env python3
"""Compatibility bridge to the canonical netmon package app."""

import importlib
import os
import sys
from runpy import run_module

NETMON_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path = [
    path
    for path in sys.path
    if os.path.abspath(path or os.getcwd()) != NETMON_REPO_ROOT
]
sys.path.insert(0, NETMON_REPO_ROOT)

if __name__ == "__main__":
    run_module("netmon.main", run_name="__main__")
else:
    app_module = importlib.import_module("netmon.app")
    sys.modules[__name__] = app_module
