"""«Повторить после обновления»: after a firmware update, find what came back and redo it.

A firmware update can re-enable apps, reset settings, bring back the stock home screen or
drop the menu's log permission. This lists what changed since the program last ran; the
caller then runs the full speed-up again, which turns all of it back on our side.
"""
from __future__ import annotations

import glob
import json
import os
from typing import Optional

from . import adb
from .backup import Session
from .i18n import tr
from .launcher import MENU_ACTIVITY, MENU_PACKAGE, current_home


def last_snapshot(session: Session) -> Optional[dict]:
    files = sorted(glob.glob(os.path.join(session.dir, "snapshots", "*.json")))
    if not files:
        return None
    with open(files[-1], encoding="utf-8") as f:
        return json.load(f)


def check(session: Session) -> dict:
    """What differs from what this program left on the TV. Changes nothing."""
    dev = session.dev
    j = session.journal()
    result = {"firmware": None, "apps": [], "settings": [], "home": None, "menu_missing": False,
              "prime_permission": False}

    last = last_snapshot(session)
    if last and last["device"].get("build") != session.info.build:
        result["firmware"] = (last["device"].get("build"), session.info.build)

    installed = set(dev.packages())
    disabled = set(dev.packages("-d"))
    result["apps"] = [p for p in j["packages"] if p in installed and p not in disabled]

    for name, value in j["values"].items():
        ns, key = name.split("/", 1)
        now = dev.get_setting(ns, key)
        if now != value:
            result["settings"].append((name, now, value))

    if MENU_PACKAGE in j["installed"]:
        if MENU_PACKAGE not in installed:
            result["menu_missing"] = True
        else:
            home = current_home(dev)
            if home and home != MENU_ACTIVITY and not home.startswith(MENU_PACKAGE + "/"):
                result["home"] = home
            perms = dev.shell(f"dumpsys package {MENU_PACKAGE}", timeout=60)
            if "android.permission.READ_LOGS: granted=true" not in perms and session.info.sdk < 33:
                result["prime_permission"] = True
    return result


def anything(result: dict) -> bool:
    return bool(result["apps"] or result["settings"] or result["home"] or result["menu_missing"]
                or result["prime_permission"])


def print_check(result: dict) -> None:
    if result["firmware"]:
        old, new = result["firmware"]
        print(tr(f"  Прошивка обновилась: {old} → {new}", f"  Firmware updated: {old} → {new}"))
    else:
        print(tr("  Прошивка та же, что при прошлом запуске.", "  Same firmware as last time."))
    if not anything(result):
        print(tr("  Ничего не вернулось — всё как после прошлого запуска.",
                 "  Nothing came back — everything is as the last run left it."))
        return
    print(tr("  Вернулось:", "  Came back:"))
    for p in result["apps"]:
        print(tr(f"    - снова включено: {p}", f"    - enabled again: {p}"))
    for name, now, ours in result["settings"]:
        print(tr(f"    - настройка {name}: {now} (было {ours})", f"    - setting {name}: {now} (was {ours})"))
    if result["home"]:
        print(tr(f"    - домашний экран: {result['home']}", f"    - home screen: {result['home']}"))
    if result["menu_missing"]:
        print(tr("    - наше меню удалено", "    - our menu was removed"))
    if result["prime_permission"]:
        print(tr("    - у меню пропало разрешение для кнопки Prime", "    - the menu lost its Prime key permission"))
