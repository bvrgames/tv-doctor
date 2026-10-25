"""Remote keys, without root, through the TV Acceleration menu.

- Netflix key: the system sends nflx://; the menu's NetflixKeyActivity takes it while Netflix
  is off or missing and opens SmartTube (only if the person installed it) or YouTube.
- Prime Video key: the system starts Prime Video by name; while Prime Video is off, the menu's
  KeyWatchService sees that start in the system log (READ_LOGS, granted here) and opens
  rus tv on a Russian-language TV, or asks once on the TV which app to open.
- rus tv: on a Russian-language TV the latest APK from github.com/bvrgames/BVR_TV is installed
  if the TV has no copy or an older one (checked against the release's SHA-256).
"""
from __future__ import annotations

import hashlib
import os
import re
import shlex
import time
import urllib.request
from typing import Optional

from . import adb
from .backup import Session, data_root
from .launcher import MENU_ACTIVITY, MENU_PACKAGE
from .keepawake import nudge
from .i18n import tr

NETFLIX = "com.netflix.ninja"
PRIME_VIDEO = "com.amazon.amazonvideo.livingroom"
RUSTV = "com.bvrgames.rustv"
RUSTV_RELEASE = "https://github.com/bvrgames/BVR_TV/releases/download/tv/"
KEY_SERVICE = f"{MENU_PACKAGE}/.KeyWatchService"


def app_enabled(dev: adb.Device, pkg: str) -> bool:
    return pkg in dev.packages() and pkg not in dev.packages("-d")


def version_code(dev: adb.Device, pkg: str) -> Optional[int]:
    m = re.search(r"versionCode=(\d+)", dev.shell(f"dumpsys package {shlex.quote(pkg)}", timeout=30))
    return int(m.group(1)) if m else None


def tv_language(dev: adb.Device) -> str:
    return (dev.getprop("persist.sys.locale") or dev.getprop("ro.product.locale") or "").split("-")[0].lower()


def _fetch(url: str, timeout: float = 120) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def install_rustv(session: Session, log=print) -> str:
    """Returns what happened, for the report."""
    dev = session.dev
    latest, sha = _fetch(RUSTV_RELEASE + "tv-version.txt", 30).decode().split()[:2]
    have = version_code(dev, RUSTV)
    if have is not None and have >= int(latest):
        return tr(f"rus tv уже последней версии ({have})", f"rus tv is up to date ({have})")
    log(tr("  Скачиваю rus tv…", "  Downloading rus tv…"))
    apk = _fetch(RUSTV_RELEASE + "rus-tv.apk")
    if hashlib.sha256(apk).hexdigest() != sha.lower():
        raise adb.AdbError(tr("rus tv: контрольная сумма скачанного файла не совпала, не устанавливаю",
                              "rus tv: the download's checksum did not match, not installing"))
    path = os.path.join(data_root(), "cache", "rus-tv.apk")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(apk)
    session.install_package(RUSTV, path)
    return tr(f"rus tv установлен (версия {latest})", f"rus tv installed (version {latest})") if have is None \
        else tr(f"rus tv обновлён: {have} → {latest}", f"rus tv updated: {have} → {latest}")


def run(session: Session, log=print) -> dict:
    dev = session.dev
    session.require_backup()
    report = {"warnings": []}

    # Netflix: the menu switches its nflx:// handler on by itself while Netflix is off
    # (the shell may not change another app's components); starting the menu applies it.
    netflix_works = app_enabled(dev, NETFLIX)
    dev.shell(f"am start -n {MENU_ACTIVITY}")
    report["netflix"] = tr("Netflix (работает сам)", "Netflix (works itself)") if netflix_works \
        else tr("YouTube (или SmartTube, если установлен)", "YouTube (or SmartTube if installed)")

    # rus tv on a Russian-language TV.
    russian = tv_language(dev) == "ru"
    if russian:
        try:
            report["rustv"] = install_rustv(session, log=log)
        except Exception as e:  # no internet, GitHub down: the rest still applies
            report["warnings"].append(tr("rus tv не установлен", "rus tv not installed") + f": {e}")

    # Prime Video: only while Prime Video itself is off or missing.
    if app_enabled(dev, PRIME_VIDEO):
        report["prime"] = tr("Prime Video (работает сам)", "Prime Video (works itself)")
        return report
    if session.info.sdk >= 33:
        report["prime"] = tr("как было (на Android 13+ это без root не сделать)", "unchanged (not possible without root on Android 13+)")
        return report
    target = RUSTV if russian and RUSTV in dev.packages() else "ask"
    # Log access is given to a process when it starts: grant first, then restart the menu.
    dev.shell(f"pm grant {MENU_PACKAGE} android.permission.READ_LOGS")
    nudge(dev)  # the screensaver lives in the menu: close it before the restart below
    dev.shell(f"am force-stop {MENU_PACKAGE}")
    dev.shell(f"am start -n {MENU_ACTIVITY} --es prime {target}")
    time.sleep(3)
    report["prime"] = "rus tv" if target == RUSTV else tr("выбор на экране ТВ при первом нажатии", "a choice on the TV at the first press")
    running = KEY_SERVICE.split("/")[1] in dev.shell(f"dumpsys activity services {MENU_PACKAGE}", timeout=30)
    if not running:
        report["warnings"].append(tr("служба кнопки Prime не запустилась", "the Prime key service did not start"))
    return report
