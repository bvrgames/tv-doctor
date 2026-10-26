"""Makes lists/lists.json — the fresh cleanup lists the program checks for at start — from
tvaccel/data/cleanyourtv. Run after updating the lists, then commit lists.json:

    python3 lists/make.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from tvaccel import cleanup  # noqa: E402

lists = cleanup.builtin_lists()
assert cleanup.valid_bundle({"lists": lists}), "the built-in lists themselves do not pass the check"
with open(os.path.join(HERE, "lists.json"), "w", encoding="utf-8") as f:
    json.dump({"lists": lists}, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
print(f"{len(lists)} lists -> lists/lists.json")
