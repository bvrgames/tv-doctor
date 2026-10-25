"""Thin wrapper around the system `adb` binary (no third-party dependencies)."""
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from typing import List, Optional

from .i18n import tr


class AdbError(RuntimeError):
    pass


def find_adb() -> str:
    path = shutil.which("adb")
    if path:
        return path
    candidates = [
        os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
        os.path.expanduser("~/Android/Sdk/platform-tools/adb"),
        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
        "/opt/homebrew/bin/adb",
        "/usr/local/bin/adb",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    raise AdbError(tr("adb не найден. Установите Android platform-tools.", "adb not found. Install Android platform-tools."))


def run_adb(args: List[str], timeout: float = 30) -> str:
    try:
        res = subprocess.run(
            [find_adb()] + args,
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise AdbError(f"adb {' '.join(args)}: " + tr("истекло время ожидания", "timed out"))
    out = (res.stdout or "") + (res.stderr or "")
    if res.returncode != 0:
        raise AdbError(out.strip() or f"adb {' '.join(args)}: " + tr("код ошибки", "exit code") + f" {res.returncode}")
    return out


def list_devices() -> List[tuple]:
    """Returns [(serial, state)], e.g. [('192.168.1.9:5555', 'device')]."""
    out = run_adb(["devices"])
    devices = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            devices.append((parts[0], parts[1]))
    return devices


def connect(host: str, port: int = 5555) -> str:
    """Returns the adb state of the device after connecting ('device', 'unauthorized', ...)."""
    target = f"{host}:{port}"
    out = run_adb(["connect", target], timeout=15)
    if "connected" not in out:
        raise AdbError(out.strip())
    for serial, state in list_devices():
        if serial == target:
            return state
    return "unknown"


def disconnect(serial: str) -> None:
    try:
        run_adb(["disconnect", serial], timeout=10)
    except AdbError:
        pass


class Device:
    def __init__(self, serial: str):
        self.serial = serial

    def shell(self, cmd: str, timeout: float = 30) -> str:
        out = run_adb(["-s", self.serial, "shell", cmd], timeout=timeout)
        return out.rstrip("\n")

    def getprop(self, name: str) -> str:
        return self.shell(f"getprop {shlex.quote(name)}").strip()

    def get_setting(self, namespace: str, key: str) -> Optional[str]:
        val = self.shell(f"settings get {namespace} {shlex.quote(key)}").strip()
        return None if val == "null" else val

    def put_setting(self, namespace: str, key: str, value: Optional[str]) -> None:
        if value is None:
            self.shell(f"settings delete {namespace} {shlex.quote(key)}")
        else:
            self.shell(f"settings put {namespace} {shlex.quote(key)} {shlex.quote(value)}")

    def list_settings(self, namespace: str) -> dict:
        out = self.shell(f"settings list {namespace}", timeout=60)
        result = {}
        for line in out.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                result[k] = v
        return result

    def packages(self, flag: str = "") -> List[str]:
        """flag: '' all, '-d' disabled, '-e' enabled, '-s' system, '-3' third-party."""
        out = self.shell(f"pm list packages {flag} --user 0", timeout=60)
        return sorted(l[len("package:"):].strip() for l in out.splitlines() if l.startswith("package:"))
