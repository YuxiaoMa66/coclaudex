#!/usr/bin/env python3
"""Self-check for codex_run.latest(). Run: python3 test_latest.py"""
import json, os, tempfile
from pathlib import Path

import codex_run as cr

with tempfile.TemporaryDirectory() as home:
    os.environ["CODEX_HOME"] = home
    cr.CFG["codex"]["auto_latest"] = True
    assert cr.latest("gpt-6-luna") == "gpt-6-luna"  # no cache: keep the config slug
    models = [("gpt-6-luna", "list"), ("gpt-5.6-luna", "list"), ("gpt-6.10-luna", "list"), ("gpt-6.9-luna", "list"),
              ("gpt-7-sol", "hide"), ("gpt-6-sol", "list"), ("gpt-7-terra", "list")]
    Path(home, "models_cache.json").write_text(json.dumps({"models": [{"slug": s, "visibility": v} for s, v in models]}))
    assert cr.latest("gpt-6-luna") == "gpt-6.10-luna"  # numeric compare: 6.10 > 6.9
    assert cr.latest("gpt-6-sol") == "gpt-6-sol"       # a hidden model is not picked
    assert cr.latest("gpt-6-astra") == "gpt-6-astra"   # family missing from the list
    assert cr.latest("chatgpt-web/x") == "chatgpt-web/x"
    cr.CFG["codex"]["auto_latest"] = False
    assert cr.latest("gpt-6-luna") == "gpt-6-luna"
print("ok")
