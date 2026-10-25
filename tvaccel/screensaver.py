"""Clock screensaver and sleep, so a still picture never stays on the screen.

The screensaver is the menu's ClockDream (a dim clock that moves every minute). Android TV
starts it after screen_off_timeout of no input and puts the TV to sleep after sleep_timeout;
an app playing video holds the screen on, so neither interrupts a film.
"""
from __future__ import annotations

from .backup import Session
from .launcher import MENU_PACKAGE

CLOCK_DREAM = f"{MENU_PACKAGE}/.ClockDream"
SCREENSAVER_AFTER_MS = 2 * 60 * 1000
SLEEP_AFTER_MS = 5 * 60 * 1000


def run(session: Session) -> dict:
    dev = session.dev
    session.require_backup()
    want = [("system", "screen_off_timeout", str(SCREENSAVER_AFTER_MS)),
            ("secure", "sleep_timeout", str(SLEEP_AFTER_MS))]
    clock = MENU_PACKAGE in dev.packages()
    if clock:
        want += [("secure", "screensaver_enabled", "1"),
                 ("secure", "screensaver_components", CLOCK_DREAM)]
    for ns, key, value in want:
        session.ensure_setting(ns, key, value)
    return {"clock": clock, "screensaver_min": SCREENSAVER_AFTER_MS // 60000, "sleep_min": SLEEP_AFTER_MS // 60000}
