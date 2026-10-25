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
from .i18n import tr

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


ROW_SIZE = 5  # apps in the menu's top row

# Never put on the top row: stores, settings, home screens, and utilities people open now and
# then (task managers, cleaners, file transfer, VPN...), matched against the package name.
NOT_FAVOURITES = {"com.android.vending", "com.android.tv.settings", "com.android.settings", MENU_PACKAGE} | set(OLD_LAUNCHERS)
UTILITY_WORDS = ("background", "process", "task", "clean", "boost", "speed", "sendfile", "file",
                 "explorer", "install", "download", "vpn", "remote", "setup", "launcher", "settings")


class MenuError(RuntimeError):
    pass


def _launchable(dev: adb.Device) -> List[str]:
    found: List[str] = []
    for category in ("LEANBACK_LAUNCHER", "LAUNCHER"):
        out = dev.shell("cmd package query-activities --brief -a android.intent.action.MAIN "
                        f"-c android.intent.category.{category}")
        for line in out.splitlines():
            pkg = line.strip().split("/")[0]
            if "/" in line and pkg not in found:
                found.append(pkg)
    return found


def _seconds(t: str) -> int:
    total = 0
    for part in t.split(":"):
        total = total * 60 + int(part or 0)
    return total


def favourite_apps(dev: adb.Device, limit: int = ROW_SIZE) -> List[str]:
    """Apps for the top row: most used first (usage stats), then most recently opened
    (recent tasks, kept across reboots), skipping utilities and system screens."""
    usage = {}
    for pkg, t in re.findall(r'package=(\S+) totalTime="([\d:]+)"', dev.shell("dumpsys usagestats", timeout=60)):
        usage[pkg] = max(usage.get(pkg, 0), _seconds(t))
    recent: List[str] = []
    for pkg in re.findall(r"\* Recent #\d+: TaskRecord\{\S+ #\d+ A=([\w.]+)", dev.shell("dumpsys activity recents", timeout=60)):
        if pkg not in recent:
            recent.append(pkg)

    candidates = [p for p in _launchable(dev)
                  if p not in NOT_FAVOURITES and not is_protected(p)
                  and not any(w in p.lower() for w in UTILITY_WORDS)]
    # Recent task affinities can carry a suffix (com.google.android.youtube.tv.main).
    def recent_rank(p: str) -> int:
        for i, r in enumerate(recent):
            if r == p or r.startswith(p + "."):
                return i
        return len(recent)

    used = sorted((p for p in candidates if usage.get(p, 0) > 0), key=lambda p: -usage[p])
    rest = sorted((p for p in candidates if p not in used and recent_rank(p) < len(recent)), key=recent_rank)
    return (used + rest)[:limit]


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
    raise MenuError(tr("Телевизор не вернулся в сеть после перезагрузки.", "The TV did not come back on the network after restarting."))


def install_menu(session: Session, apk: str = MENU_APK, reboot_check: bool = True,
                 log=print) -> dict:
    """Returns {'installed': bool, 'disabled': [...], 'home': str}."""
    dev = session.dev
    if not os.path.isfile(apk):
        raise MenuError(tr("Нет файла меню", "Menu file missing") + f": {apk}")
    session.require_backup()
    previous_home = current_home(dev)

    first_install = MENU_PACKAGE not in dev.packages()
    log(tr("  Устанавливаю новое меню…", "  Installing the new menu…"))
    session.install_package(MENU_PACKAGE, apk)
    if first_install:
        # Only on the first install, so a row the person arranged later is never overwritten.
        apps = favourite_apps(dev)
        if apps:
            log(tr("  Приложения в верхнем ряду", "  Apps on the top row") + f": {', '.join(apps)}")
            dev.shell(f"am start -n {MENU_ACTIVITY} --es apps {','.join(apps)} --es stamp {int(time.time())}")
    set_home(dev, MENU_ACTIVITY)

    disabled: List[str] = []
    try:
        if not home_opens_menu(dev):
            raise MenuError(tr("кнопка «Домой» открывает не новое меню", "Home does not open the new menu"))
        log(tr("  Новое меню открывается — отключаю старый домашний экран…",
               "  The new menu opens — turning off the old home screen…"))
        for pkg in old_launchers(dev):
            if session.disable_package(pkg):
                disabled.append(pkg)
        if disabled:
            time.sleep(15)  # Android writes package state a few seconds later
        set_home(dev, MENU_ACTIVITY)
        if not home_opens_menu(dev):
            raise MenuError(tr("после отключения старого экрана «Домой» не открывает новое меню",
                                "with the old home screen off, Home does not open the new menu"))
        if reboot_check:
            log(tr("  Перезагружаю ТВ, чтобы проверить запуск меню после включения…",
                   "  Restarting the TV to check the menu comes up after a restart…"))
            adb.run_adb(["-s", dev.serial, "reboot"], timeout=20)
            dev = session.dev = wait_for_boot(dev.serial)
            if not foreground(dev).startswith(MENU_PACKAGE + "/") and not home_opens_menu(dev):
                raise MenuError(tr("после перезагрузки открылось не новое меню", "after the restart, something else opened"))
    except (MenuError, adb.AdbError) as e:
        log(tr(f"  Не получилось ({e}). Возвращаю старый домашний экран…", f"  That failed ({e}). Bringing back the old home screen…"))
        _undo(session, disabled, previous_home)
        raise MenuError(tr(f"Меню не установлено: {e}. Всё возвращено как было.", f"Menu not installed: {e}. Everything was put back."))

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
