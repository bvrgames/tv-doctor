"""Get adb when the computer has none: Google's platform-tools, downloaded on first use.

adb is not shipped with the program (Google's own distribution terms); it is fetched from
dl.google.com into ~/.tv-acceleration/platform-tools.
"""
from __future__ import annotations

import io
import os
import platform
import stat
import urllib.request
import zipfile

from .backup import data_root

URL = "https://dl.google.com/android/repository/platform-tools-latest-{}.zip"


def local_adb() -> str:
    exe = "adb.exe" if platform.system() == "Windows" else "adb"
    return os.path.join(data_root(), "platform-tools", exe)


def download(log=print) -> str:
    system = {"Windows": "windows", "Darwin": "darwin", "Linux": "linux"}.get(platform.system())
    if not system:
        raise RuntimeError(f"no platform-tools for {platform.system()}")
    from .i18n import tr
    log(tr("  Скачиваю adb с сайта Google (один раз)…", "  Downloading adb from Google (once)…"))
    with urllib.request.urlopen(URL.format(system), timeout=300) as r:
        data = r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(data_root())
    path = local_adb()
    if system != "windows":
        for name in os.listdir(os.path.dirname(path)):
            p = os.path.join(os.path.dirname(path), name)
            if os.path.isfile(p):
                os.chmod(p, os.stat(p).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path
