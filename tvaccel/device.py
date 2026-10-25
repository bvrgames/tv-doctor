"""Device identification: model, Android version, manufacturer, RAM."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .adb import Device

# Nominal RAM sizes sold on TV devices, in GB. MemTotal is always a bit below
# the nominal size (kernel/GPU reservations), so we round up to the nearest one.
_NOMINAL_GB = [0.5, 1, 1.5, 2, 3, 4, 6, 8, 12, 16]


@dataclass
class DeviceInfo:
    serial: str
    device_id: str      # stable id used for the backup folder
    manufacturer: str
    brand: str
    model: str
    device: str
    android_version: str
    sdk: int
    build: str
    ram_total_mb: int
    ram_available_mb: int
    ram_nominal_gb: float
    is_tv: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _meminfo(dev: Device) -> dict:
    out = dev.shell("cat /proc/meminfo")
    info = {}
    for line in out.splitlines():
        m = re.match(r"(\w+):\s+(\d+)\s*kB", line)
        if m:
            info[m.group(1)] = int(m.group(2))
    return info


def nominal_gb(total_mb: int) -> float:
    gb = total_mb / 1024
    for n in _NOMINAL_GB:
        if gb <= n:
            return n
    return round(gb)


def detect(dev: Device) -> DeviceInfo:
    props = {}
    for line in dev.shell("getprop").splitlines():
        m = re.match(r"\[(.+?)\]: \[(.*)\]", line)
        if m:
            props[m.group(1)] = m.group(2)

    mem = _meminfo(dev)
    total_mb = mem.get("MemTotal", 0) // 1024
    avail_mb = mem.get("MemAvailable", mem.get("MemFree", 0)) // 1024

    features = dev.shell("pm list features")
    is_tv = "android.software.leanback" in features or "android.hardware.type.television" in features

    serial_no = props.get("ro.serialno") or props.get("ro.boot.serialno") or dev.serial
    model = props.get("ro.product.model", "")
    device_id = re.sub(r"[^A-Za-z0-9._-]", "_", f"{model}_{serial_no}")

    return DeviceInfo(
        serial=dev.serial,
        device_id=device_id,
        manufacturer=props.get("ro.product.manufacturer", ""),
        brand=props.get("ro.product.brand", ""),
        model=model,
        device=props.get("ro.product.device", ""),
        android_version=props.get("ro.build.version.release", ""),
        sdk=int(props.get("ro.build.version.sdk", "0") or 0),
        build=props.get("ro.build.display.id", ""),
        ram_total_mb=total_mb,
        ram_available_mb=avail_mb,
        ram_nominal_gb=nominal_gb(total_mb),
        is_tv=is_tv,
    )
