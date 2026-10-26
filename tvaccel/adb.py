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
    from . import adbget  # here, not at the top: adbget -> backup -> adb
    for c in candidates + [adbget.local_adb()]:
        if os.path.isfile(c):
            return c
    try:
        return adbget.download()
    except Exception as e:
        raise AdbError(tr("adb не найден и не скачался: ", "adb not found and could not be downloaded: ") + str(e))


# On an Android phone there is no adb program: the phone app's Java side (AdbBridge, built on
# libadb-android) speaks the adb protocol, and run_adb() is answered through it.
ON_ANDROID = "ANDROID_DATA" in os.environ and "ANDROID_ROOT" in os.environ
_EXIT = "__TVACCEL_EXIT__"


def _run_on_phone(args: List[str], timeout: float) -> str:
    from java import jclass  # Chaquopy
    bridge = jclass("com.bvrgames.tvaccel.phone.AdbBridge")
    if args[:1] == ["-s"]:
        args = args[2:]  # the phone holds one connection: the TV it found
    cmd = args[0]
    try:
        if cmd == "devices":
            serial = bridge.connectedSerial()
            return "List of devices attached\n" + (f"{serial}\tdevice\n" if serial else "")
        if cmd == "connect":
            host, _, port = args[1].partition(":")
            state = bridge.connect(host, int(port or 5555), int(timeout * 1000))
            if state == "unauthorized":
                raise AdbError("unauthorized")
            return f"connected to {args[1]}"
        if cmd == "disconnect":
            bridge.disconnect()
            return ""
        if cmd == "shell":
            out = str(bridge.shell(f"{args[1]}; echo {_EXIT}$?", int(timeout * 1000)))
            body, found, code = out.rpartition(_EXIT)
            if not found:  # the answer was cut off: do not take half an answer for a success
                raise AdbError("the TV's answer was cut off")
            if code.strip() != "0":
                raise AdbError(body.strip() or f"exit code {code.strip()}")
            return body
        if cmd == "install":
            out = str(bridge.install(args[-1], int(timeout * 1000)))
            if "Success" not in out:
                raise AdbError(out.strip())
            return out
        if cmd == "uninstall":
            return str(bridge.shell(f"pm uninstall {args[1]}", int(timeout * 1000)))
        if cmd == "reboot":
            bridge.reboot()
            return ""
    except AdbError:
        raise
    except Exception as e:  # Java exceptions: lost connection, timeout
        raise AdbError(str(e))
    raise AdbError(f"adb {cmd}: not supported on the phone")


def run_adb(args: List[str], timeout: float = 30) -> str:
    if ON_ANDROID:
        return _run_on_phone(args, timeout)
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


def wait_online(serial: str, timeout: float = 90) -> bool:
    """Make sure the TV answers; after a dropped connection, reconnect (network serials) until it does."""
    import time
    host, _, port = serial.partition(":")
    try:  # still connected: keep it (on the phone a reconnect costs a new connection)
        if Device(serial).shell("echo ok", timeout=10).strip() == "ok":
            return True
    except AdbError:
        pass
    deadline = time.time() + timeout
    tries = 0
    while time.time() < deadline:
        tries += 1
        if tries == 3 and not ON_ANDROID:
            # The computer itself rejoined Wi-Fi (new address): the adb server keeps a dead
            # route ("No route to host") until it is restarted.
            try:
                run_adb(["kill-server"], timeout=10)
                run_adb(["start-server"], timeout=20)
            except AdbError:
                pass
        try:
            if port:
                run_adb(["disconnect", serial], timeout=10)
                connect(host, int(port))
            if Device(serial).shell("echo ok", timeout=10).strip() == "ok":
                return True
        except AdbError:
            pass
        time.sleep(5)
    return False


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
