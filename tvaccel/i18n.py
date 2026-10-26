"""Language of everything the program says: Russian or English.

Until a TV is found: the language the person picked with the RU / EN switch (remembered),
else the language of the computer or phone. Once a TV is found, the TV's language, as before;
the switch still changes it after that.
"""
from __future__ import annotations

import json
import locale
import os

_lang = None
_system = None   # what the window reports (the browser's or phone's language): more reliable than LANG,
                 # which an app opened from Finder does not have


def _choice_file() -> str:
    from .backup import data_root  # here: backup imports adb, which imports this module
    return os.path.join(data_root(), "language.json")


def saved_choice():
    try:
        with open(_choice_file(), encoding="utf-8") as f:
            value = json.load(f).get("lang")
        return value if value in ("ru", "en") else None
    except (OSError, ValueError):
        return None


def choose(value: str) -> str:
    """The RU / EN switch: use it now and remember it for the next start."""
    global _lang
    _lang = "ru" if value == "ru" else "en"
    try:
        os.makedirs(os.path.dirname(_choice_file()), exist_ok=True)
        with open(_choice_file(), "w", encoding="utf-8") as f:
            json.dump({"lang": _lang}, f)
    except OSError:
        pass
    return _lang


def set_system(tag: str) -> None:
    global _system
    _system = "ru" if (tag or "").lower().startswith("ru") else "en"


def _computer_is_russian() -> bool:
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        if os.environ.get(var):
            return os.environ[var].lower().startswith("ru")
    try:
        return (locale.getlocale()[0] or "").lower().startswith("ru")
    except ValueError:
        return False


def set_from_tv(dev) -> str:
    global _lang
    tag = dev.getprop("persist.sys.locale") or dev.getprop("ro.product.locale") or ""
    _lang = "ru" if tag.lower().startswith("ru") else "en"
    return _lang


def lang() -> str:
    return _lang or saved_choice() or _system or ("ru" if _computer_is_russian() else "en")


def tr(ru: str, en: str) -> str:
    return ru if lang() == "ru" else en
