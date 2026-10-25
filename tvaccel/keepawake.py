"""Keep the TV out of its screensaver and sleep while the program works.

adb commands don't count as someone using the TV, so during a run Android would start the
clock screensaver after 2 minutes; restarting the menu then ends the screensaver, and Android
takes that as the moment to sleep: Wi-Fi goes off mid-run. A key with no meaning anywhere
(KEYCODE_UNKNOWN) counts as use: sent at the start and every 30 s, it resets the idle timer
and closes a screensaver already showing. KEYCODE_WAKEUP does not: it only wakes a sleeping TV.
"""
from __future__ import annotations

import threading

from . import adb

NUDGE = "input keyevent KEYCODE_UNKNOWN"
EVERY_S = 30


def nudge(dev: adb.Device) -> None:
    """One poke: wake a sleeping TV, end a screensaver, reset the idle timer."""
    try:
        dev.shell("input keyevent KEYCODE_WAKEUP; " + NUDGE, timeout=15)
    except adb.AdbError:
        pass  # offline for a moment (a restart in the run): the next poke tries again


class KeepAwake:
    """with KeepAwake(session): ... — pokes the TV every 30 s until the block ends."""

    def __init__(self, session):
        self.session = session
        self.stop = threading.Event()

    def _loop(self):
        while not self.stop.wait(EVERY_S):
            nudge(self.session.dev)  # session.dev: the run may reconnect and replace it

    def __enter__(self):
        nudge(self.session.dev)
        threading.Thread(target=self._loop, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self.stop.set()
        return False
