"""Проверка безопасности (a security check, not an antivirus). It only looks, it changes nothing.

1. Known malware for TV boxes: file paths, package names and APK SHA-1s from Doctor Web's public
   indicators (https://github.com/DoctorWebLtd/malware-iocs), fetched at run time and cached for a day.
2. Signs of a tampered firmware: su binaries, debuggable or insecure build, test keys.
3. Apps installed from outside Play Store.
4. Risky access held by apps: microphone, camera, location, contacts, SMS, drawing over other
   apps, installing apps, accessibility, device admin, notification access, VPN.
5. Microphone and viewing tracking (ACR), the way cleanyourtv's tools/privacy.py does it
   (MIT, Gathin): the voice service the firmware names, known ACR/telemetry packages, and the
   AppOps history of RECORD_AUDIO. Packages sharing the system UID are not counted as listeners.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import time
import urllib.request
from typing import Dict, List, Optional, Set

from . import adb
from .backup import data_root
from .i18n import tr
from .launcher import MENU_PACKAGE

IOC_REPO = "DoctorWebLtd/malware-iocs"
IOC_CACHE_HOURS = 24
# Malware also replaces genuine files; there only the hash can tell, not the path.
NORMAL_SYSTEM_PLACES = ("/system/lib", "/system/app/", "/system/priv-app/", "/system/framework/", "/vendor/")
SYSTEM_UID = 1000
OURS = {MENU_PACKAGE}

# From cleanyourtv tools/privacy.py (MIT): packages with a known job, by evidence, not by name.
# package: (category, Russian note, English note)
CATALOGUE = {
    "com.google.android.katniss": ("voice", "Google Ассистент и голосовой поиск (кнопка микрофона на пульте)", "Google Assistant and voice search (the remote's mic button)"),
    "com.google.android.speech.pumpkin": ("voice", "офлайн-модель «Окей, Google»", 'offline "Ok Google" model'),
    "org.droidtv.amazonalexa": ("voice", "Amazon Alexa на Philips", "Amazon Alexa on Philips"),
    "tv.inscape.tvclient.inscapeacr": ("acr", "Inscape ACR: узнаёт, что на экране (включая HDMI)", "Inscape ACR: identifies what is on screen (HDMI too)"),
    "com.skyworth.aisense": ("acr", "ACR Coocaa/Skyworth для рекламы", "Coocaa/Skyworth ACR for ads"),
    "tv.samba.ssm.ui": ("acr", "Samba TV ACR на TCL: узнаёт, что на экране, для рекламы", "Samba TV ACR on TCL: identifies what is on screen for ads"),
    "tv.alphonso.alphonso_eula": ("acr", "Alphonso ACR: узнаёт, что смотрят", "Alphonso ACR: identifies what you watch"),
    "org.droidtv.candeebug": ("telemetry", "аналитика Philips (DAC)", "Philips analytics (DAC)"),
    "org.droidtv.gel": ("telemetry", "аналитика Philips (GEL)", "Philips analytics (GEL)"),
    "org.droidtv.usagelogger": ("telemetry", "статистика загрузок и нажатий пульта Philips", "Philips boot and remote keypress stats"),
    "org.droidtv.tv.frameworklogger": ("telemetry", "журналирование Philips", "Philips logging"),
    "com.tcl.logkit": ("telemetry", "сбор и отправка журналов TCL", "TCL log capture and upload"),
    "com.google.android.feedback": ("telemetry", "отчёты в Google", "reports to Google"),
    "com.miui.tv.analytics": ("telemetry", "аналитика Xiaomi", "Xiaomi analytics"),
}
NAME_HINT = re.compile(r"(?:^|\.)(acr|analytics|hotword|inscape|listen|microphone|telemetry|tracker|tracking)",
                       re.IGNORECASE)
VOICE_SETTINGS = ("voice_interaction_service", "voice_recognition_service", "assistant")

RISKY = {
    "android.permission.RECORD_AUDIO": ("микрофон", "microphone"),
    "android.permission.CAMERA": ("камера", "camera"),
    "android.permission.ACCESS_FINE_LOCATION": ("точное местоположение", "precise location"),
    "android.permission.ACCESS_COARSE_LOCATION": ("местоположение", "location"),
    "android.permission.READ_CONTACTS": ("контакты", "contacts"),
    "android.permission.READ_SMS": ("SMS", "SMS"),
    "android.permission.READ_CALL_LOG": ("журнал звонков", "call log"),
}


# ---- known malware -------------------------------------------------------------
def _fetch(url: str, timeout: float = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "tv-doctor"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def malware_indicators(log=print) -> Optional[dict]:
    """{'sha1': set, 'packages': set, 'paths': set, 'families': int} from Doctor Web, cached."""
    cache = os.path.join(data_root(), "cache", "malware-iocs.json")
    if os.path.exists(cache) and time.time() - os.path.getmtime(cache) < IOC_CACHE_HOURS * 3600:
        with open(cache, encoding="utf-8") as f:
            d = json.load(f)
        return {k: set(v) if isinstance(v, list) else v for k, v in d.items()}
    try:
        folders = [e["name"] for e in json.loads(_fetch(f"https://api.github.com/repos/{IOC_REPO}/contents"))
                   if e.get("type") == "dir" and e["name"].lower().startswith("android")]
    except Exception:
        return None
    sha1, packages, paths = set(), set(), set()
    for name in folders:
        try:
            text = _fetch(f"https://raw.githubusercontent.com/{IOC_REPO}/master/{name}/README.adoc")
        except Exception:
            try:
                text = _fetch(f"https://raw.githubusercontent.com/{IOC_REPO}/main/{name}/README.adoc")
            except Exception:
                continue
        samples = re.split(r"(?im)^==\s*network indicators", text)[0]  # skip the domain lists
        sha1 |= {h.lower() for h in re.findall(r"\b[0-9a-fA-F]{40}\b", samples)}
        packages |= set(re.findall(r"\b([a-z][a-z0-9_]*(?:\.[a-z0-9_]+){2,})\s*\(apk\)", samples))
        packages |= set(re.findall(r"variants\s*\(([a-z][a-z0-9_]*(?:\.[a-z0-9_]+){2,})\)", samples))
        paths |= set(re.findall(r"(/(?:system|data|vendor)/[\w./-]+)", samples))
    d = {"sha1": sorted(sha1), "packages": sorted(packages), "paths": sorted(paths), "families": len(folders)}
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(d, f)
    return {k: set(v) if isinstance(v, list) else v for k, v in d.items()}


# ---- helpers ------------------------------------------------------------------------
def _exists(dev: adb.Device, path: str) -> bool:
    return dev.shell(f"[ -e {shlex.quote(path)} ] && echo yes || echo no").strip() == "yes"


def _quiet(dev: adb.Device, cmd: str, timeout: float = 60) -> str:
    """Shell output, or '' if the command fails on this firmware."""
    try:
        return dev.shell(cmd, timeout=timeout)
    except adb.AdbError:
        return ""


def _dump(dev: adb.Device, pkg: str) -> str:
    return dev.shell(f"dumpsys package {shlex.quote(pkg)}", timeout=60)


def _uid(dump: str) -> Optional[int]:
    m = re.search(r"\buserId=(\d+)", dump)
    return int(m.group(1)) if m else None


def _granted_runtime(dump: str) -> Set[str]:
    block = dump.split("runtime permissions:", 1)[-1] if "runtime permissions:" in dump else ""
    return set(re.findall(r"(android\.permission\.[A-Z_]+): granted=true", block))


def used_microphone(ops: str) -> Optional[bool]:
    """From cleanyourtv privacy.py: True for recorded access, False for none, None if unknown."""
    if not ops or "error" in ops.lower() or "exception" in ops.lower():
        return None
    lines = [line.strip() for line in ops.splitlines()]
    for line in lines:
        if line.startswith("RECORD_AUDIO: ") and (line.endswith(" (running)") or re.search(
                r"; time=(?:0|[+-](?:\d+[dhms])*\d+ms) ago(?:;| \(running\)|$)", line)):
            return True
    return False if "No operations." in lines or any(l.startswith("RECORD_AUDIO: ") for l in lines) else None


def _components(value: Optional[str]) -> List[str]:
    if not value or value == "null":
        return []
    return [c.split("/")[0] for c in re.split(r"[:,]", value) if "/" in c]


# ---- the check ----------------------------------------------------------------------
def run(dev: adb.Device, log=print) -> dict:
    r: Dict[str, object] = {"malware": [], "firmware": [], "not_from_play": [], "risky": [],
                            "voice": [], "acr": [], "telemetry": [], "mic_used": [], "notes": []}
    installed = dev.packages()
    disabled = set(dev.packages("-d"))
    third = [p for p in dev.packages("-3") if p not in OURS]

    # 1. Known malware.
    ioc = malware_indicators(log=log)
    if ioc is None:
        r["notes"].append(tr("Не удалось скачать список известных вирусов (нет интернета?) — эта часть пропущена.",
                             "Could not download the known-malware list (no internet?) — that part was skipped."))
    else:
        r["ioc_families"] = ioc["families"]
        for p in sorted(ioc["packages"] & set(installed)):
            r["malware"].append(tr(f"приложение {p} — из списка Dr.Web", f"app {p} — on the Dr.Web list"))
        for path in sorted(ioc["paths"]):
            if not _exists(dev, path):
                continue
            if path.startswith(NORMAL_SYSTEM_PLACES):
                # A real Android file the malware replaces (libcutils.so, DeskClock.apk...):
                # only its contents tell, so it counts only if the hash is a known sample.
                out = _quiet(dev, f"sha1sum {shlex.quote(path)}", 120).split()
                if out and out[0].lower() in ioc["sha1"]:
                    r["malware"].append(tr(f"файл {path} заменён заражённым (совпал с образцом Dr.Web)",
                                             f"file {path} was replaced by an infected one (matches a Dr.Web sample)"))
            else:
                r["malware"].append(tr(f"файл {path} — такого файла в чистой прошивке нет (список Dr.Web)",
                                         f"file {path} — not part of a clean firmware (Dr.Web list)"))
        for p in third:
            for apk in [l.split(":", 1)[1] for l in dev.shell(f"pm path {p}").splitlines() if l.startswith("package:")]:
                out = _quiet(dev, f"sha1sum {shlex.quote(apk)}", 120).split()
                if out and out[0].lower() in ioc["sha1"]:
                    r["malware"].append(tr(f"приложение {p} — его файл совпал с образцом из списка Dr.Web",
                                             f"app {p} — its file matches a Dr.Web sample"))

    # 2. Firmware.
    if dev.getprop("ro.debuggable") == "1":
        r["firmware"].append(tr("прошивка в отладочном режиме (ro.debuggable=1)", "debuggable firmware (ro.debuggable=1)"))
    if dev.getprop("ro.secure") == "0":
        r["firmware"].append(tr("защита прошивки выключена (ro.secure=0)", "firmware security off (ro.secure=0)"))
    if "test-keys" in dev.getprop("ro.build.tags"):
        r["firmware"].append(tr("прошивка подписана тестовыми ключами (test-keys)", "firmware signed with test keys"))
    for su in ("/system/xbin/su", "/system/bin/su", "/sbin/su", "/system/xbin/daemonsu"):
        if _exists(dev, su):
            r["firmware"].append(tr(f"найден {su} (root)", f"found {su} (root)"))

    # 3. Not from Play Store.
    for line in dev.shell("pm list packages -3 -i").splitlines():
        m = re.match(r"package:(\S+)\s+installer=(\S+)", line)
        if m and m.group(1) not in OURS and m.group(2) != "com.android.vending":
            how = tr("установлено через adb или файлом", "installed over adb or from a file") if m.group(2) in ("null", "com.google.android.packageinstaller",
                                                                      "com.android.packageinstaller") \
                else (tr("обновляет себя само", "updates itself") if m.group(2) == m.group(1)
                      else tr("установщик", "installer") + f" {m.group(2)}")
            r["not_from_play"].append(f"{m.group(1)} — {how}")

    # 4. Risky access (third-party apps; system apps under uid 1000 would all "have" everything).
    can_install = set(_quiet(dev, "appops query-op REQUEST_INSTALL_PACKAGES allow").split())
    overlay = set(_quiet(dev, "appops query-op SYSTEM_ALERT_WINDOW allow").split())
    accessibility = _components(dev.get_setting("secure", "enabled_accessibility_services"))
    listeners = _components(dev.get_setting("secure", "enabled_notification_listeners"))
    admins = set(re.findall(r"admin=ComponentInfo\{([\w.]+)/", _quiet(dev, "dumpsys device_policy", 30)))
    vpn = _quiet(dev, "dumpsys connectivity")
    for p in third:
        dump = _dump(dev, p)
        what = [tr(*RISKY[x]) for x in sorted(_granted_runtime(dump)) if x in RISKY]
        if p in can_install:
            what.append(tr("может устанавливать другие приложения", "can install other apps"))
        if p in overlay:
            what.append(tr("может рисовать поверх других приложений", "can draw over other apps"))
        if p in accessibility:
            what.append(tr("включены специальные возможности (видит всё на экране и нажатия)",
                           "accessibility service on (sees the screen and key presses)"))
        if p in admins:
            what.append(tr("администратор устройства", "device admin"))
        if p in listeners:
            what.append(tr("читает уведомления", "reads notifications"))
        if re.search(rf"VPN.*{re.escape(p)}", vpn):
            what.append("VPN")
        if what:
            r["risky"].append(f"{p}: {', '.join(what)}")

    # 5. Microphone and viewing tracking.
    owners: Dict[str, List[str]] = {}
    for key in VOICE_SETTINGS:
        v = dev.get_setting("secure", key)
        if v and "/" in v:
            owners.setdefault(v.split("/")[0], []).append(key)
    names = [p for p in installed if p in CATALOGUE or p in owners or NAME_HINT.search(p)]
    for p in names[:25]:
        category, note_ru, note_en = CATALOGUE.get(p, ("voice" if p in owners else "unknown", "совпало только по названию",
                                                       "matched by name only"))
        note = tr(note_ru, note_en)
        state = tr("отключено", "disabled") if p in disabled else tr("работает", "enabled")
        line = f"{p} ({state}) — {note}"
        dump = _dump(dev, p)
        if _uid(dump) == SYSTEM_UID:
            line += tr("; системный пакет, его права — права системы, а не признак записи",
                       "; system package: its permissions are the system's, not a sign of recording")
        mic = used_microphone(_quiet(dev, f"appops get {shlex.quote(p)} RECORD_AUDIO"))
        if mic:
            r["mic_used"].append(p)
            line += tr("; ЕСТЬ недавнее обращение к микрофону", "; RECENT microphone access")
        r.setdefault(category if category in ("voice", "acr", "telemetry") else "telemetry", []).append(line)
    for p in third:
        if p not in names and used_microphone(_quiet(dev, f"appops get {shlex.quote(p)} RECORD_AUDIO")):
            r["mic_used"].append(p)
    return r
