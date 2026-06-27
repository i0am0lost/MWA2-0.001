#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_root.py - resolve the PROJECT ROOT (the folder that holds school/ + jail/) regardless of how deep the
app code lives. The Python tooling sits under <root>/system/app/, so ROOT is found by walking up from here
until a directory containing both world folders is seen. Every tool imports ROOT from here instead of
assuming its own dir is the root -- keeps paths correct after the deep reorg and portable when copied."""
import os


def _find_root():
    here = os.path.dirname(os.path.abspath(__file__))   # <root>/system/app
    cur = here
    for _ in range(8):
        if os.path.isdir(os.path.join(cur, "school")) and os.path.isdir(os.path.join(cur, "jail")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.dirname(os.path.dirname(here))       # fallback: app -> system -> root


ROOT = _find_root()
