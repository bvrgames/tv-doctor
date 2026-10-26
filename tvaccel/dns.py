"""Ad blocking with Android's Private DNS (AdGuard DNS, DNS-over-TLS on port 853).

Private DNS exists from Android 9. In "hostname" mode Android sends every lookup to that
server only, so if it can't be reached the TV loses the internet: the change is checked
right away and undone if the TV no longer gets online.
"""
from __future__ import annotations

import random
import re
import time

from . import adb, net
from .backup import Session
from .i18n import tr

ADGUARD = "dns.adguard-dns.com"
AD_PROBES = ("googleads.g.doubleclick.net", "pagead2.googlesyndication.com", "app-measurement.com")
# Fresh names every time (GitHub Pages answers any *.github.io), so the TV's DNS cache
# can't hide a server that doesn't work.
FRESH_PROBE = "tvaccel-{}.github.io"
BLOCKED_ADDRESSES = ("0.0.0.0", "127.0.0.1", "::")


def resolve(dev: adb.Device, host: str) -> str:
    """The address the TV resolves host to, or '' if it can't."""
    try:
        out = dev.shell(f"ping -c1 -W2 {host} 2>&1 | head -1", timeout=10)
    except adb.AdbError:  # the lookup itself hung: no answer
        return ""
    m = re.search(r"\(([0-9a-f.:]+)\)", out)
    return m.group(1) if m else ""


def private_dns_state(dev: adb.Device) -> dict:
    out = dev.shell("dumpsys connectivity", timeout=60)
    active = re.search(r"UsePrivateDns: (\w+) PrivateDnsServerName: (\S+)", out)
    return {"in_use": bool(active) and active.group(1) == "true",
            "server": active.group(2) if active else None}


def run(session: Session, log=print) -> dict:
    dev = session.dev
    report = {"supported": session.info.sdk >= 28, "enabled": False, "blocked": 0, "warnings": []}
    if not report["supported"]:
        report["warnings"].append(tr("Частный DNS появился в Android 9, на этом устройстве блокировка рекламы недоступна.",
                                     "Private DNS needs Android 9 or later: ad blocking is not available on this device."))
        return report

    old_mode = dev.get_setting("global", "private_dns_mode")
    old_host = dev.get_setting("global", "private_dns_specifier")
    if old_mode == "hostname" and old_host and old_host != ADGUARD:
        report["warnings"].append(tr(f"Уже настроен свой частный DNS ({old_host}) — не меняю.",
                                     f"A custom Private DNS is already set ({old_host}) — left as is."))
        return report

    # No internet on the TV at all: nothing to check AdGuard with, and nothing to block.
    if not any(resolve(dev, h) for h in (FRESH_PROBE.format(random.randrange(10**9)), "ya.ru")):
        text = tr("У телевизора сейчас нет интернета — блокировка рекламы (AdGuard DNS) не включена.",
                  "The TV has no internet right now — ad blocking (AdGuard DNS) was not turned on.")
        report["warnings"].append(text)
        net.skip(text)
        return report

    session.require_backup()
    session.ensure_setting("global", "private_dns_specifier", ADGUARD)
    session.ensure_setting("global", "private_dns_mode", "hostname")

    ok = False
    for _ in range(5):
        time.sleep(3)
        state = private_dns_state(dev)
        fresh = FRESH_PROBE.format(random.randrange(10**9))
        if state["in_use"] and state["server"] == ADGUARD and \
                resolve(dev, fresh) not in ("",) + BLOCKED_ADDRESSES:
            ok = True
            break
    if not ok:
        dev.put_setting("global", "private_dns_mode", old_mode)
        dev.put_setting("global", "private_dns_specifier", old_host)
        session.forget_value("global", "private_dns_mode")
        session.forget_value("global", "private_dns_specifier")
        report["warnings"].append(tr("AdGuard DNS недоступен из этой сети (возможно, порт 853 закрыт) — "
                                     "настройка возвращена, интернет работает как раньше.",
                                     "AdGuard DNS is not reachable from this network (port 853 may be blocked) — "
                                     "the setting was put back, the internet works as before."))
        return report

    report["enabled"] = True
    report["blocked"] = sum(resolve(dev, h) in BLOCKED_ADDRESSES for h in AD_PROBES)
    report["probes"] = len(AD_PROBES)
    return report
