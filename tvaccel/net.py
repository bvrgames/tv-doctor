"""Everything the program fetches from the internet, and the addresses, in one place.

The internet is optional: GitHub often does not open in Russia, or crawls. Every fetch has a
short time limit for the whole download (not per read), and the caller carries on without
that step.
"""
from __future__ import annotations

import gzip
import time
import urllib.request
from typing import List, Optional

# Fresh cleanup lists (lists/lists.json in this repository; made by lists/make.py).
LISTS_URLS = ["https://raw.githubusercontent.com/bvrgames/tv-doctor/main/lists/lists.json"]

TIMEOUT = 5  # seconds to connect and get the first answer


class NetError(OSError):
    pass


def fetch(urls: List[str], limit: float = 8, timeout: float = TIMEOUT, headers: Optional[dict] = None) -> bytes:
    """The first address that answers in time; NetError if none does. `limit`: seconds for the
    whole download from one address, so a crawling connection gives up too."""
    errors = []
    for url in urls:
        if not url:
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "tv-doctor", "Accept-Encoding": "gzip",
                                                       **(headers or {})})
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
                if r.headers.get("Content-Encoding") == "gzip":
                    data = gzip.decompress(data)
                return data
        except Exception as e:
            errors.append(f"{url}: {e}")
    raise NetError("; ".join(errors) or "no address")
