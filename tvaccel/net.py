"""Everything the program fetches from the internet, and the addresses, in one place.

The internet is optional: GitHub often does not open in Russia, or crawls. Every fetch has a
hard time limit (looking up the address included, which a socket timeout does not cover), and
the caller carries on without that step; what was skipped is collected in SKIPPED for the
report. Cleanup, the menu, the screensaver, the remote keys and Undo need no internet.
"""
from __future__ import annotations

import gzip
import threading
import time
import urllib.request
from typing import List, Optional

# Backup download addresses, used when the main one does not answer (a folder URL ending in "/").
RUSTV_MIRROR = ""  # holds tv-version.txt and rus-tv.apk, like the BVR_TV release
ADB_MIRROR = ""    # holds platform-tools-latest-<windows|darwin|linux>.zip

# Fresh cleanup lists (lists/lists.json in this repository; made by lists/make.py).
LISTS_URLS = ["https://raw.githubusercontent.com/bvrgames/tv-doctor/main/lists/lists.json"]
RUSTV_URLS = ["https://github.com/bvrgames/BVR_TV/releases/download/tv/", RUSTV_MIRROR]
ADB_URLS = ["https://dl.google.com/android/repository/", ADB_MIRROR]
IOC_REPO = "DoctorWebLtd/malware-iocs"  # Dr.Web's known malware for Android
IOC_FOLDERS_URL = f"https://api.github.com/repos/{IOC_REPO}/contents"
IOC_FILE_URLS = [f"https://raw.githubusercontent.com/{IOC_REPO}/master/{{}}/README.adoc",
                 f"https://raw.githubusercontent.com/{IOC_REPO}/main/{{}}/README.adoc"]
GEO_URL = "http://ip-api.com/json/?fields=status,country,countryCode,proxy,hosting"  # country for Wi-Fi

TIMEOUT = 5  # seconds without an answer (connecting, or the download stalls)

SKIPPED: List[str] = []  # plain words for the report: what this run did without


class NetError(OSError):
    pass


def skip(text: str) -> None:
    if text not in SKIPPED:
        SKIPPED.append(text)


def _get(url: str, limit: float, timeout: float, headers: dict) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "tv-doctor", "Accept-Encoding": "gzip", **headers})
    deadline = time.time() + limit
    with urllib.request.urlopen(req, timeout=timeout) as r:
        parts = []
        while True:
            if time.time() > deadline:
                raise NetError(f"too slow (over {limit:g} s)")
            chunk = r.read1(64 * 1024)  # what has come, so the time check runs
            if not chunk:
                break
            parts.append(chunk)
        data = b"".join(parts)
        return gzip.decompress(data) if r.headers.get("Content-Encoding") == "gzip" else data


def fetch(urls: List[str], limit: float = 8, timeout: float = TIMEOUT, headers: Optional[dict] = None) -> bytes:
    """The first address that answers; NetError if none does. `limit`: seconds for one address,
    all of it, so a crawling or silent connection gives up too."""
    errors = []
    for url in urls:
        if not url:
            continue
        box: dict = {}

        def work():
            try:
                box["data"] = _get(url, limit, timeout, headers or {})
            except Exception as e:
                box["error"] = e

        t = threading.Thread(target=work, daemon=True)  # left behind if it overruns: it ends by itself
        t.start()
        t.join(limit + 1)
        if "data" in box:
            return box["data"]
        errors.append(f"{url}: {box.get('error') or 'no answer'}")
    raise NetError("; ".join(errors) or "no address")
