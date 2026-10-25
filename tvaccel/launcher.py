"""Install the TV Acceleration menu and make it the home screen, safely.

Order matters: the old home screen is turned off only after Home is seen opening the new
menu. If any check fails, everything done here is undone automatically.
"""
from __future__ import annotations

import os
import re
import shlex
import time
from typing import List, Optional

from . import adb
from .backup import HOME_QUERY, Session
from .protected import is_protected

MENU_PACKAGE = "com.bvrgames.tvaccel.home"
MENU_ACTIVITY = f"{MENU_PACKAGE}/.MainActivity"
MENU_APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "launcher", "out", "tv-accel-menu.apk")

# Home screens that are safe to turn off once ours works (from tv-detox install.sh,
# plus tv-detox's own menu). Google TV's launcherx is protected and never turned off.
OLD_LAUNCHERS = [
    "com.google.android.tvlauncher",
    "com.google.android.leanbacklauncher",
    "com.mitv.tvhome",
    "com.amazon.tv.launcher",
    "com.ansub.tvhome",
]


class MenuError(RuntimeError):
    pass


def current_home(dev: adb.Device) -> str:
    lines = dev.shell(HOME_QUERY).strip().splitlines()
    return lines[-1].strip() if lines else ""


def foreground(dev: adb.Device) -> str:
    """The package/activity in front, e.g. 'com.bvrgames.tvaccel.home/.MainActivity'."""
    for cmd, pattern in (("dumpsys activity activities", r"(?:mResumedActivity|topResumedActivity)"),
                         ("dumpsys window windows", r"mCurrentFocus")):
        for line in dev.shell(cmd, timeout=30).splitlines():
            if re.search(pattern, line):
                m = re.search(r"([\w.]+)/([\w.$]+)", line)
                if m:
                    return f"{m.group(1)}/{m.group(2)}"
    return ""


def home_opens_menu(dev: adb.Device, tries: int = 6) -> bool:
    """Leave the home screen, press Home, and check our menu comes to the front."""
    dev.shell("am start -W -a android.settings.SETTINGS")
    time.sleep(2)
    dev.shell("input keyevent KEYCODE_HOME")
    for _ in range(tries):
        time.sleep(1.5)
        if foreground(dev).startswith(MENU_PACKAGE + "/"):
            return True
    return False


def _persistent(dev: adb.Device, package: str) -> bool:
    out = dev.shell(f"dumpsys package {shlex.quote(package)}", timeout=30)
    m = re.search(r"pkgFlags=\[([^\]]*)\]", out)
    return m is None or "PERSISTENT" in m.group(1)


def old_launchers(dev: adb.Device) -> List[str]:
    out = dev.shell("cmd package query-activities --brief -a android.intent.action.MAIN "
                    "-c android.intent.category.HOME")
    homes = {l.strip().split("/")[0] for l in out.splitlines() if "/" in l}
    return [p for p in OLD_LAUNCHERS
            if p in homes and not is_protected(p) and not _persistent(dev, p)]


def set_home(dev: adb.Device, activity: str) -> None:
    if not activity or "/" not in activity:
        return
    if int(dev.getprop("ro.build.version.sdk") or 0) >= 29:
        dev.shell(f"cmd role add-role-holder --user 0 android.app.role.HOME {activity.split('/')[0]}")
    dev.shell(f"cmd package set-home-activity {shlex.quote(activity)}")


def wait_for_boot(serial: str, timeout: float = 240) -> adb.Device:
    host, _, port = serial.partition(":")
    deadline = time.time() + timeout
    time.sleep(20)
    while time.time() < deadline:
        try:
            if port:
                adb.connect(host, int(port))
            dev = adb.Device(serial)
            if dev.getprop("sys.boot_completed") == "1":
                time.sleep(15)  # let the home screen start
                return dev
        except adb.AdbError:
            pass
        time.sleep(5)
    raise MenuError("Телевизор не вернулся в сеть после перезагрузки.")


def install_menu(session: Session, apk: str = MENU_APK, reboot_check: bool = True,
                 log=print) -> dict:
    """Returns {'installed': bool, 'disabled': [...], 'home': str}."""
    dev = session.dev
    if not os.path.isfile(apk):
        raise MenuError(f"Нет файла меню: {apk}")
    session.require_backup()
    previous_home = current_home(dev)

    log("  Устанавливаю новое меню…")
    session.install_package(MENU_PACKAGE, apk)
    set_home(dev, MENU_ACTIVITY)

    disabled: List[str] = []
    try:
        if not home_opens_menu(dev):
            raise MenuError("кнопка «Домой» открывает не новое меню")
        log("  Новое меню открывается — отключаю старый домашний экран…")
        for pkg in old_launchers(dev):
            if session.disable_package(pkg):
                disabled.append(pkg)
        if disabled:
            time.sleep(15)  # Android writes package state a few seconds later
        set_home(dev, MENU_ACTIVITY)
        if not home_opens_menu(dev):
            raise MenuError("после отключения старого экрана «Домой» не открывает новое меню")
        if reboot_check:
            log("  Перезагружаю ТВ, чтобы проверить запуск меню после включения…")
            adb.run_adb(["-s", dev.serial, "reboot"], timeout=20)
            dev = session.dev = wait_for_boot(dev.serial)
            if not foreground(dev).startswith(MENU_PACKAGE + "/") and not home_opens_menu(dev):
                raise MenuError("после перезагрузки открылось не новое меню")
    except (MenuError, adb.AdbError) as e:
        log(f"  Не получилось ({e}). Возвращаю старый домашний экран…")
        _undo(session, disabled, previous_home)
        raise MenuError(f"Меню не установлено: {e}. Всё возвращено как было.")

    return {"installed": True, "disabled": disabled, "home": current_home(dev)}


def _undo(session: Session, disabled: List[str], previous_home: str) -> None:
    dev = session.dev
    for pkg in disabled:
        try:
            dev.shell(f"pm enable --user 0 {shlex.quote(pkg)}")
        except adb.AdbError:
            pass
    set_home(dev, previous_home)
    session.uninstall_ours(MENU_PACKAGE)
    dev.shell("input keyevent KEYCODE_HOME")
