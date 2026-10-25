"""Wi-Fi: diagnostics, no false "no internet", and the 5 GHz region fix.

The region fix is for devices bought in another country (a Mi TV Stick from Russia used in
Indonesia does not see 5 GHz channels 149-161). On Xiaomi sticks the Wi-Fi region is
`settings put global service_region XX` (uppercase; lowercase is reset at boot), source:
https://sites.google.com/site/tweakradje/devices/xiaomi-mi-tv-stick
It is changed only when the region differs from the country AND a 5 GHz network the
computer sees is missing on the TV, and kept only if the TV then sees it.
"""
from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import time
import urllib.request
from typing import List, Optional, Set

from . import adb
from .backup import Session
from .i18n import tr

REGION_KEY = "service_region"
GEO_URL = "http://ip-api.com/json/?fields=status,country,countryCode,proxy,hosting"


def channel(freq: int) -> int:
    if 2412 <= freq <= 2484:
        return 14 if freq == 2484 else (freq - 2407) // 5
    if 5000 <= freq <= 5900:
        return (freq - 5000) // 5
    return 0


# ---- what the TV sees ------------------------------------------------------
def connection(dev: adb.Device) -> dict:
    out = dev.shell("dumpsys wifi", timeout=60)
    m = re.search(r"mWifiInfo SSID: (.*?), BSSID: ([0-9a-f:]+).*?RSSI: (-?\d+), Link speed: (\d+)Mbps, "
                  r"Frequency: (\d+)MHz", out)
    if not m:
        return {}
    freq = int(m.group(5))
    return {"ssid": m.group(1), "bssid": m.group(2), "rssi": int(m.group(3)),
            "speed": int(m.group(4)), "freq": freq, "channel": channel(freq)}


def tv_scan(dev: adb.Device) -> List[dict]:
    out = dev.shell("dumpsys wifiscanner", timeout=60)
    block = out.split("Latest native scan results:", 1)[-1].split("Latest native pno", 1)[0]
    nets = []
    for m in re.finditer(r"^\s+([0-9a-f:]{17})\s+(\d+)\s+(-?\d+)\s+\S+\s+(.*?)\s+(\[.*)?$", block, re.M):
        freq = int(m.group(2))
        nets.append({"bssid": m.group(1), "freq": freq, "rssi": int(m.group(3)),
                     "ssid": m.group(4).strip(), "channel": channel(freq)})
    return nets


def signal_quality(rssi: int) -> str:
    if rssi >= -55:
        return tr("отличный", "excellent")
    if rssi >= -67:
        return tr("хороший", "good")
    if rssi >= -75:
        return tr("слабый", "weak")
    return tr("очень слабый", "very weak")


# ---- what the computer sees -----------------------------------------------
def computer_5ghz_channels() -> Optional[Set[int]]:
    """5 GHz channels the computer running this tool can see; None if it can't scan."""
    system = platform.system()
    try:
        if system == "Darwin":
            out = subprocess.run(["system_profiler", "SPAirPortDataType"], capture_output=True,
                                 text=True, timeout=60).stdout
            chans = re.findall(r"Channel: (\d+) \(5GHz", out)
        elif system == "Windows":
            out = subprocess.run(["netsh", "wlan", "show", "networks", "mode=bssid"], capture_output=True,
                                 text=True, timeout=60).stdout
            chans = re.findall(r"(?:Channel|Канал)\s*:\s*(\d+)", out)
        elif system == "Linux":
            out = subprocess.run(["nmcli", "-t", "-f", "CHAN", "dev", "wifi"], capture_output=True,
                                 text=True, timeout=60).stdout
            chans = out.split()
        else:
            return None
    except (OSError, subprocess.SubprocessError):
        return None
    found = {int(c) for c in chans if c.isdigit() and int(c) >= 32}
    return found if found or "Channel" in out else None


# ---- country ---------------------------------------------------------------
def _tz_country(tz: str) -> Optional[str]:
    for path in ("/usr/share/zoneinfo/zone.tab", "/usr/share/zoneinfo/zone1970.tab"):
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    parts = line.split("\t")
                    if len(parts) >= 3 and parts[2].strip() == tz:
                        return parts[0].split(",")[0].upper()
        except OSError:
            continue
    return None


def _local_tz() -> Optional[str]:
    """The computer's own time zone name (the TV's may still be the one from the shop)."""
    tz = os.environ.get("TZ")
    if tz:
        return tz
    try:
        target = os.path.realpath("/etc/localtime")
        return target.split("zoneinfo/", 1)[1] if "zoneinfo/" in target else None
    except OSError:
        return None


def country(session: Session, ask=input, log=print) -> Optional[str]:
    """Country by internet address. If it looks like a VPN, ask once and remember."""
    saved_path = os.path.join(session.dir, "country.json")
    if os.path.exists(saved_path):
        with open(saved_path, encoding="utf-8") as f:
            return json.load(f).get("country")
    try:
        with urllib.request.urlopen(GEO_URL, timeout=10) as r:
            geo = json.load(r)
    except Exception:
        return None
    if geo.get("status") != "success":
        return None
    code, name = geo["countryCode"].upper(), geo.get("country", geo["countryCode"])
    tz = _local_tz()
    tz_country = _tz_country(tz) if tz else None
    suspicious = geo.get("proxy") or geo.get("hosting") or (tz_country and tz_country != code)
    if suspicious:
        answer = ask(tr(f"  Ваша страна: {name}? [Enter — да, или введите код страны, например ID]: ",
                        f"  Is your country {name}? [Enter — yes, or type a country code, e.g. ID]: ")).strip()
        if answer and answer.lower() not in ("y", "yes", "да", "д"):
            code = answer.upper()[:2]
    os.makedirs(session.dir, exist_ok=True)
    with open(saved_path, "w", encoding="utf-8") as f:
        json.dump({"country": code}, f)
    return code


# ---- changes ---------------------------------------------------------------
def restart_wifi(session: Session) -> adb.Device:
    """Turns Wi-Fi off and on from the TV itself (adb over Wi-Fi drops meanwhile)."""
    dev = session.dev
    dev.shell("nohup sh -c 'svc wifi disable; sleep 4; svc wifi enable' >/dev/null 2>&1 &")
    host, _, port = dev.serial.partition(":")
    deadline = time.time() + 90
    time.sleep(20)
    while time.time() < deadline:
        try:
            if port:
                adb.connect(host, int(port))
            if connection(dev):
                time.sleep(15)  # let a scan finish
                return dev
        except adb.AdbError:
            pass
        time.sleep(5)
    raise adb.AdbError(tr("Телевизор не вернулся в Wi-Fi после перезапуска.", "The TV did not rejoin Wi-Fi after the restart."))


def run(session: Session, ask=input, log=print) -> dict:
    dev = session.dev
    session.require_backup()
    report = {"connection": connection(dev), "warnings": [], "region_changed": None}

    # False "no internet": the check for a captive portal, which also fails where Google is blocked.
    session.ensure_setting("global", "captive_portal_mode", "0")
    report["captive_portal_off"] = True

    region = dev.get_setting("global", REGION_KEY)
    report["region"] = region
    tv_chans = {n["channel"] for n in tv_scan(dev) if n["freq"] >= 5000}
    pc_chans = computer_5ghz_channels()
    missing = sorted(pc_chans - tv_chans) if pc_chans is not None else []
    report["tv_5ghz"], report["pc_5ghz"], report["missing_5ghz"] = sorted(tv_chans), pc_chans, missing

    if region is None:
        if missing:
            chans = ", ".join(map(str, missing))
            report["warnings"].append(tr(f"ТВ не видит сети 5 ГГц на каналах {chans}, "
                                         "а смена региона на этом устройстве не поддерживается.",
                                         f"The TV does not see 5 GHz networks on channels {chans}, "
                                         "and this device can't change its Wi-Fi region."))
        return report

    code = country(session, ask=ask, log=log)
    report["country"] = code
    if not code or region.upper() == code:
        if ["global", REGION_KEY] in session.journal()["settings"]:
            session.ensure_setting("global", REGION_KEY, region)  # ours from an earlier run: watch it
        return report
    if pc_chans is None:
        report["warnings"].append(tr(f"Регион Wi-Fi устройства {region.upper()}, а страна {code}. "
                                     "Проверить 5 ГГц не удалось: этот компьютер не умеет сканировать Wi-Fi.",
                                     f"The device's Wi-Fi region is {region.upper()}, the country is {code}. "
                                     "Could not check 5 GHz: this computer can't scan Wi-Fi."))
        return report
    if not missing:
        return report  # region differs, but nothing is actually missing: leave it

    chans = ", ".join(map(str, missing))
    log(tr(f"  Регион Wi-Fi {region.upper()} ≠ {code}, ТВ не видит 5 ГГц (каналы {chans}). Меняю регион на {code}…",
           f"  Wi-Fi region {region.upper()} ≠ {code}, the TV misses 5 GHz (channels {chans}). "
           f"Changing the region to {code}…"))
    session.put_setting("global", REGION_KEY, code)
    session.dev = dev = restart_wifi(session)
    seen = {n["channel"] for n in tv_scan(dev) if n["freq"] >= 5000}
    if set(missing) & seen:
        report["region_changed"] = (region, code)
        report["tv_5ghz"] = sorted(seen)
    else:
        dev.put_setting("global", REGION_KEY, region)
        session.forget_value("global", REGION_KEY)
        session.dev = restart_wifi(session)
        report["warnings"].append(tr(f"Смена региона на {code} не помогла увидеть 5 ГГц — регион возвращён.",
                                     f"Changing the region to {code} did not reveal 5 GHz — region put back."))
    return report
