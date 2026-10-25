"""Language of everything the program says: Russian if the TV is in Russian, else English.

Until a TV is found (connection errors) the computer's own language decides.
"""
from __future__ import annotations

import locale
import os

_lang = None


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
    return _lang or ("ru" if _computer_is_russian() else "en")


def tr(ru: str, en: str) -> str:
    return ru if lang() == "ru" else en
