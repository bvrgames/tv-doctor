"""Cleanup «максимум»: junk, ads and telemetry by the model lists from cleanyourtv,
app caches, faster animations, and a background-process limit on weak devices.

Model lists: tvaccel/data/cleanyourtv/<model>/debloat.txt, from
https://github.com/Gathin23/cleanyourtv (MIT, see data/cleanyourtv/LICENSE).
At start the program also checks for fresher lists in this repository (lists/lists.json, see
net.LISTS_URLS) for a few seconds; no answer or a broken file — the built-in ones are used.
The protected list (protected.py) always comes from the program and applies over any list.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from collections import Counter
from typing import Dict, List, Optional, Tuple

from . import adb, net
from .backup import Session
from .launcher import NOT_FAVOURITES, _launchable, favourite_apps
from .protected import is_protected
from .i18n import tr

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "cleanyourtv")

ANIMATION_SCALE = "0.5"
ANIMATION_KEYS = ("window_animation_scale", "transition_animation_scale", "animator_duration_scale")

# Background process limit, only on weak devices.
LOW_RAM_GB = 1.5          # limit when nominal RAM is this or less
MAX_CACHED_PROCESSES = 4  # Android 9 default is 32; 8 changed nothing on a 1 GB stick

# Lists for other models of the same brand, or the generic fallback, never take these:
# features people use without ever "opening" an app (casting, voice, accessibility, updates).
FALLBACK_KEEP = {
    "com.google.android.apps.mediashell", "com.mitv.milinkservice", "com.google.android.katniss",
    "com.google.android.speech.pumpkin", "com.google.android.tts", "com.google.android.marvin.talkback",
    "com.google.android.tv.remote.service", "com.google.android.tv.assistant",
    "com.xiaomi.mitv.updateservice",
}
# Screensavers are left for the screensaver step (clock and sleep), not removed here.
SCREENSAVERS = {"com.android.dreams.basic", "com.mitv.dream", "com.google.android.backdrop",
                "com.google.android.apps.tv.dreamx"}
# Live Channels is protected (HDMI inputs), but useless where there are no inputs at all.
LIVE_CHANNELS = "com.google.android.tv"
COMMON_MIN_LISTS = 15  # a package in this many model lists counts as generic junk
BRAND_MIN_LISTS = 2    # for an unknown model: in this many lists of the same brand


PACKAGE = re.compile(r"^[A-Za-z][\w.]*$")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def parse_list(path: str) -> List[str]:
    pkgs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if line and PACKAGE.match(line.split()[0]):
                pkgs.append(line.split()[0])
    return pkgs


MIN_LISTS = 50  # a fresh file with fewer lists than this is cut short, not fresh


def builtin_lists() -> Dict[str, dict]:
    """{folder: {"brand": maker from tv.json, "pkgs": [...]}}"""
    lists = {}
    for name in sorted(os.listdir(DATA)):
        path = os.path.join(DATA, name, "debloat.txt")
        if os.path.isfile(path):
            try:
                with open(os.path.join(DATA, name, "tv.json"), encoding="utf-8") as f:
                    brand = json.load(f).get("brand", "")
            except (OSError, ValueError):
                brand = ""
            lists[name] = {"brand": brand, "pkgs": parse_list(path)}
    return lists


def valid_bundle(data) -> bool:
    """A downloaded lists file is used only if every list in it is well-formed."""
    lists = data.get("lists") if isinstance(data, dict) else None
    if not isinstance(lists, dict) or len(lists) < MIN_LISTS:
        return False
    for name, l in lists.items():
        if not (isinstance(name, str) and isinstance(l, dict) and isinstance(l.get("brand"), str)
                and isinstance(l.get("pkgs"), list) and l["pkgs"]
                and all(isinstance(p, str) and PACKAGE.match(p) for p in l["pkgs"])):
            return False
    return True


_fresh: Optional[Dict[str, dict]] = None
_checked = threading.Event()
_checking = False
_failed = False


def start_update() -> None:
    """At program start: look for fresh lists in the background (a few seconds at most)."""
    global _checking
    if _checking:
        return
    _checking = True

    def check():
        global _fresh, _failed
        try:
            raw = net.fetch(net.LISTS_URLS)
        except Exception:  # no answer: the built-in lists
            _failed = True
            raw = None
        try:
            data = json.loads(raw.decode("utf-8")) if raw else None
            if valid_bundle(data):  # broken: ignored, the built-in lists
                _fresh = data["lists"]
        except ValueError:
            pass
        finally:
            _checked.set()

    threading.Thread(target=check, daemon=True).start()


def all_lists() -> Dict[str, dict]:
    """The built-in lists, with fresh ones from the repository over them when they came."""
    if _checking:
        _checked.wait(12)  # the check itself gives up sooner
    if _checking and _failed:
        net.skip(tr("Свежие списки приложений не скачались — использованы встроенные в программу.",
                    "Fresh app lists did not download — the ones built into the program were used."))
    lists = builtin_lists()
    if _fresh:
        lists.update(_fresh)
    return lists


def lists_fresh() -> bool:
    return bool(_fresh)


def pick_list(model: str, makers: List[str], android: str, lists: Dict[str, dict]) -> Tuple[str, List[str]]:
    """Returns (source, packages). The model's own list only if the maker matches too (one model
    name can belong to two makers), else this maker's common junk + generic junk."""
    m = _slug(model)
    ours = {_slug(x) for x in makers if x}
    exact = [n for n, l in lists.items() if (n == m or n.endswith("-" + m) or ("-" + m + "-") in n)
             and _slug(l["brand"]) in ours]
    if exact:
        # Several firmwares of one model: prefer the folder naming our Android version.
        exact.sort(key=lambda n: (f"android{android}" not in n, len(n)))
        return exact[0], lists[exact[0]]["pkgs"]

    counts = Counter(p for l in lists.values() for p in set(l["pkgs"]))
    brand_counts = Counter(p for l in lists.values() if _slug(l["brand"]) in ours for p in set(l["pkgs"]))
    pkgs = {p for p, c in counts.items() if c >= COMMON_MIN_LISTS}
    pkgs |= {p for p, c in brand_counts.items() if c >= BRAND_MIN_LISTS}
    maker = next((x for x in makers if x), "")
    return tr("общий список", "generic list") + f" ({maker or tr('неизвестный производитель', 'unknown maker')})", \
        sorted(pkgs - FALLBACK_KEEP)


def has_tv_inputs(dev: adb.Device) -> bool:
    """True if the TV input framework knows any input (HDMI, tuner...). When unsure, True."""
    out = dev.shell("dumpsys tv_input", timeout=30)
    sections = {"inputMap:": "packageSet:", "mHardwareList:": "mHdmiDeviceList:"}
    lines = out.splitlines()
    found_any = False
    for start, end in sections.items():
        inside = False
        for line in lines:
            if start in line:
                inside, found_any = True, True
                continue
            if inside and end in line:
                inside = False
            elif inside and line.strip():
                return True
    return not found_any


def preinstalled(dev: adb.Device) -> set:
    return set(dev.packages("-s"))


def plan(session: Session) -> dict:
    """What cleanup would do, without changing anything."""
    dev, info = session.dev, session.info
    source, wanted = pick_list(info.model, [info.brand, info.manufacturer], info.android_version, all_lists())
    installed = set(dev.packages())
    disabled = set(dev.packages("-d"))
    system = preinstalled(dev)
    launchable = set(_launchable(dev))
    in_use = set(favourite_apps(dev, limit=100))
    home = session.dev.shell("cmd package resolve-activity --brief -a android.intent.action.MAIN "
                             "-c android.intent.category.HOME").strip().splitlines()
    home_pkg = home[-1].split("/")[0] if home else ""

    no_inputs = LIVE_CHANNELS in installed and not has_tv_inputs(dev)
    if no_inputs and LIVE_CHANNELS not in wanted:
        wanted = list(wanted) + [LIVE_CHANNELS]

    result = {"source": source, "disable": [], "already": [], "protected": [], "in_use": [], "not_system": []}
    for p in wanted:
        if p not in installed:
            continue
        if p in disabled:
            result["already"].append(p)
        elif p == LIVE_CHANNELS and no_inputs and p not in in_use and p in system:
            result["disable"].append(p)
        elif is_protected(p) or p == home_pkg or p in NOT_FAVOURITES - {"com.google.android.tvlauncher"}:
            result["protected"].append(p)
        elif p in SCREENSAVERS:
            continue
        elif p in in_use:
            result["in_use"].append(p)
        elif p not in system and p in launchable:  # an app the person may have installed
            result["not_system"].append(p)
        else:
            result["disable"].append(p)
    return result


def background_limit_needed(info) -> bool:
    return info.ram_nominal_gb <= LOW_RAM_GB


def data_free_mb(dev: adb.Device) -> Optional[int]:
    out = dev.shell("df -k /data").splitlines()
    try:
        return int(out[-1].split()[3]) // 1024
    except (IndexError, ValueError):
        return None


def run(session: Session, log=print) -> dict:
    dev = session.dev
    session.require_backup()
    p = plan(session)
    report = dict(p)
    report["disabled_now"] = []
    for pkg in p["disable"]:
        if session.disable_package(pkg, allow_protected=(pkg == LIVE_CHANNELS)):
            report["disabled_now"].append(pkg)
    if report["disabled_now"]:
        time.sleep(20)  # Android writes package state ~10 s later; a reboot before that undoes it

    before = data_free_mb(dev)
    dev.shell("pm trim-caches 999G", timeout=120)
    after = data_free_mb(dev)
    report["cache_freed_mb"] = (after - before) if before is not None and after is not None else None

    for key in ANIMATION_KEYS:
        session.ensure_setting("global", key, ANIMATION_SCALE)
    report["animation_scale"] = ANIMATION_SCALE

    report["ram_gb"] = session.info.ram_nominal_gb
    report["bg_limit"] = background_limit_needed(session.info)
    if report["bg_limit"]:
        # The setting is a comma-separated key=value list; keep anything else already in it.
        current = dev.get_setting("global", "activity_manager_constants") or ""
        parts = [kv for kv in current.split(",") if kv and not kv.startswith("max_cached_processes=")]
        parts.append(f"max_cached_processes={MAX_CACHED_PROCESSES}")
        session.ensure_setting("global", "activity_manager_constants", ",".join(parts))
    return report
