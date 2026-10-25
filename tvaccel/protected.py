"""Packages that must never be disabled, whatever any cleanup list says."""
from __future__ import annotations

import fnmatch

PROTECTED_PATTERNS = [
    # Core Android
    "android",
    "com.android.systemui",
    "com.android.shell",              # adb itself runs through it
    "com.android.providers.*",
    "com.android.packageinstaller",
    "com.google.android.packageinstaller",
    "com.android.externalstorage",
    "com.android.server.*",
    "com.android.networkstack*",
    "com.android.wifi*",
    "com.android.certinstaller",
    "com.android.keychain",
    "com.android.location.fused",
    "com.android.tv.provision",
    "com.android.defcontainer",       # needed to install apps
    "com.google.android.webview",
    "com.android.captiveportallogin",
    "com.android.inputdevices",       # remote/keyboard key layouts
    # Settings
    "com.android.settings",
    "com.android.tv.settings",
    "com.google.android.tv.settings*",
    "*.tvsettings*",
    # Google services and Play Store
    "com.google.android.gms",
    "com.google.android.gsf*",
    "com.android.vending",
    "com.google.android.ext.services",
    "com.google.android.ext.shared",
    "com.google.android.tungsten.setupwraith",
    "com.google.android.apps.tv.launcherx",  # Google TV home is also its setup host
    "com.google.android.katniss",            # voice search from the remote mic button
    "com.google.android.speech.pumpkin",
    # Keyboard / input methods
    "com.google.android.leanback.ime",
    "com.google.android.inputmethod.*",
    "com.android.inputmethod.*",
    "*keyboard*",
    "*.ime",
    # Remote control and Bluetooth
    "com.android.bluetooth*",
    "com.google.android.tv.remote.service",
    "com.google.android.tv.bluetooth*",
    "com.google.android.tv.remote*",
    "*remotecontrol*",
    "*.rcu*",
    # HDMI / TV inputs
    "com.android.tv",
    "com.google.android.tv",                 # TV input framework / Live Channels
    "*tvinput*",
    "*hdmi*",
    "com.google.android.tv.frameworkpackagestubs",
    # Vendor boot services
    "*xiaomi.tvservice*",
    "*droidlogic*",
    "mitv.service",
    "com.xiaomi.mitv.res",
]


def is_protected(package: str) -> bool:
    p = package.lower()
    return any(fnmatch.fnmatchcase(p, pat) for pat in PROTECTED_PATTERNS)
