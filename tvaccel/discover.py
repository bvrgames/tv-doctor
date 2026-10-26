"""Find an Android TV with network debugging enabled on the local network."""
from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from . import adb
from .i18n import tr

ADB_PORT = 5555


class NotFound(adb.AdbError):
    """No TV answers on the network (off, another Wi-Fi, or debugging still off)."""


class NeedsOk(adb.AdbError):
    """The TV is showing "Allow debugging?" and waits for OK. .serial: that TV."""
    serial = ""


def local_ipv4() -> Optional[str]:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # no packets are sent for UDP connect
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def _port_open(host: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def scan_subnet(port: int = ADB_PORT, timeout: float = 0.6) -> List[str]:
    """Hosts in our /24 with the adb port open."""
    me = local_ipv4()
    if not me:
        return []
    net = ipaddress.ip_network(f"{me}/24", strict=False)
    hosts = [str(h) for h in net.hosts() if str(h) != me]
    with ThreadPoolExecutor(max_workers=64) as pool:
        flags = list(pool.map(lambda h: _port_open(h, port, timeout), hosts))
    return [h for h, ok in zip(hosts, flags) if ok]


def _connect(host: str, port: int) -> str:
    try:
        return adb.connect(host, port)
    except adb.AdbError as e:
        if str(e) == "unauthorized":  # the phone's adb says so with an error, not a state
            return "unauthorized"
        raise


def find_tv(host: Optional[str] = None) -> adb.Device:
    """Connect to `host`, or to an already connected device, or scan the network."""
    if host:
        h, _, p = host.partition(":")
        state = _connect(h, int(p or ADB_PORT))
        return _ready(f"{h}:{p or ADB_PORT}", state)

    ready = [s for s, st in adb.list_devices() if st == "device"]
    if len(ready) == 1:
        return adb.Device(ready[0])

    candidates = scan_subnet()
    if not candidates:
        raise NotFound(
            tr("Телевизор не найден в сети. Проверьте, что он включён, подключён к той же "
               "сети Wi-Fi и что на нём включена отладка по сети.",
               "No TV found on the network. Check that it is on, on the same Wi-Fi network, "
               "and that network debugging is turned on.")
        )
    errors = []
    for h in candidates:
        try:
            return _ready(f"{h}:{ADB_PORT}", _connect(h, ADB_PORT))
        except NeedsOk:
            raise
        except adb.AdbError as e:
            errors.append(f"{h}: {e}")
    raise NotFound(tr("Не удалось подключиться:", "Could not connect:") + "\n" + "\n".join(errors))


def _ready(serial: str, state: str) -> adb.Device:
    if state == "unauthorized":
        e = NeedsOk(
            tr("На экране телевизора появился запрос «Разрешить отладку?». "
               "Отметьте «Всегда разрешать с этого компьютера», нажмите «ОК» и запустите ещё раз.",
               "The TV is asking \"Allow USB debugging?\". Tick \"Always allow from this computer\", "
               "press OK and run this again.")
        )
        e.serial = serial  # ask this TV again, without scanning
        raise e
    if state != "device":
        raise adb.AdbError(f"{serial}: " + tr(f"устройство в состоянии «{state}»", f"device is \"{state}\""))
    return adb.Device(serial)
