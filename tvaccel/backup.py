"""Backup before any change, and one-step rollback to the original state.

Layout (on the computer/phone running the tool, not on the TV):
    ~/.tv-acceleration/<device_id>/
        original.json        first snapshot ever taken, never overwritten
        snapshots/<ts>.json  snapshot taken before every run
        journal.json         every setting/package we touched since the last rollback

Rollback returns every touched setting and the enabled/disabled state of every
package to what `original.json` recorded.
"""
from __future__ import annotations

import json
import os
import shlex
import time
from typing import List, Optional

from .adb import AdbError, Device
from .device import DeviceInfo, detect
from .protected import is_protected

NAMESPACES = ("global", "secure", "system")
HOME_QUERY = "cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME"


def data_root() -> str:
    return os.environ.get("TV_ACCEL_HOME") or os.path.join(os.path.expanduser("~"), ".tv-acceleration")


def _write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _read_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def take_snapshot(dev: Device, info: DeviceInfo) -> dict:
    home = dev.shell(HOME_QUERY).strip().splitlines()
    return {
        "taken_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "device": info.to_dict(),
        "packages": dev.packages(),
        "disabled": dev.packages("-d"),
        "home_activity": home[-1] if home else "",
        "settings": {ns: dev.list_settings(ns) for ns in NAMESPACES},
    }


class Session:
    """All changes to the TV go through this class, so each one is backed up first."""

    def __init__(self, dev: Device, info: Optional[DeviceInfo] = None):
        self.dev = dev
        self.info = info or detect(dev)
        self.dir = os.path.join(data_root(), self.info.device_id)
        self.original_path = os.path.join(self.dir, "original.json")
        self.journal_path = os.path.join(self.dir, "journal.json")
        self._backed_up = False

    # ---- backup -------------------------------------------------------
    def has_original(self) -> bool:
        return os.path.exists(self.original_path)

    def original(self) -> dict:
        data = _read_json(self.original_path)
        if data is None:
            raise AdbError("Резервная копия не найдена — откатывать нечего.")
        return data

    def backup(self) -> str:
        """Snapshot the TV. The very first snapshot becomes original.json."""
        snap = take_snapshot(self.dev, self.info)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        path = os.path.join(self.dir, "snapshots", f"{stamp}.json")
        _write_json(path, snap)
        if not self.has_original():
            _write_json(self.original_path, snap)
        self._backed_up = True
        return path

    def _require_backup(self) -> None:
        if not self._backed_up:
            self.backup()

    # ---- journal ------------------------------------------------------
    def journal(self) -> dict:
        return _read_json(self.journal_path, {"settings": [], "packages": []})

    def _record(self, kind: str, item) -> None:
        j = self.journal()
        if item not in j[kind]:
            j[kind].append(item)
            _write_json(self.journal_path, j)

    # ---- changes ------------------------------------------------------
    def put_setting(self, namespace: str, key: str, value: Optional[str]) -> None:
        self._require_backup()
        self._record("settings", [namespace, key])
        self.dev.put_setting(namespace, key, value)

    def disable_package(self, package: str) -> bool:
        """pm disable-user only, never uninstall. Returns False if skipped."""
        if is_protected(package):
            return False
        if package not in self.dev.packages() or package in self.dev.packages("-d"):
            return False
        self._require_backup()
        self._record("packages", package)
        out = self.dev.shell(f"pm disable-user --user 0 {shlex.quote(package)}")
        return "disabled" in out

    # ---- rollback -----------------------------------------------------
    def restore(self) -> dict:
        """Return touched settings and all package states to original.json."""
        orig = self.original()
        report = {"settings": [], "enabled": [], "disabled": [], "errors": []}

        for ns, key in self.journal()["settings"]:
            old = orig["settings"].get(ns, {}).get(key)
            try:
                if self.dev.get_setting(ns, key) != old:
                    self.dev.put_setting(ns, key, old)
                    report["settings"].append(f"{ns}/{key} = {old if old is not None else '(нет)'}")
            except AdbError as e:
                report["errors"].append(f"{ns}/{key}: {e}")

        installed = set(self.dev.packages())
        now_disabled = set(self.dev.packages("-d"))
        was_disabled = set(orig["disabled"])

        for pkg in sorted(now_disabled - was_disabled):
            try:
                self.dev.shell(f"pm enable --user 0 {shlex.quote(pkg)}")
                report["enabled"].append(pkg)
            except AdbError as e:
                report["errors"].append(f"{pkg}: {e}")

        for pkg in sorted((was_disabled - now_disabled) & installed):
            try:
                self.dev.shell(f"pm disable-user --user 0 {shlex.quote(pkg)}")
                report["disabled"].append(pkg)
            except AdbError as e:
                report["errors"].append(f"{pkg}: {e}")

        if not report["errors"]:
            _write_json(self.journal_path, {"settings": [], "packages": []})
        return report

    def verify_restored(self) -> List[str]:
        """Differences that remain between the TV and original.json."""
        orig = self.original()
        diffs = []
        now_disabled = set(self.dev.packages("-d"))
        installed = set(self.dev.packages())
        was_disabled = set(orig["disabled"])
        for pkg in sorted(now_disabled - was_disabled):
            diffs.append(f"всё ещё отключено: {pkg}")
        for pkg in sorted((was_disabled - now_disabled) & installed):
            diffs.append(f"было отключено, сейчас включено: {pkg}")
        return diffs
