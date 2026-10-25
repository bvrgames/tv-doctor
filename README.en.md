# TV Acceleration

[Русский](README.md) · **English**

Speed up and clean an Android TV or Google TV — sticks, boxes and TVs — with one button.

You turn on debugging on the TV (the program shows how, with pictures) and press **Speed up**.
The program does the rest and ends with a before/after report.

Three buttons:

- **Speed up** — everything below;
- **Repeat after an update** — if a firmware update brought something back, the program finds it and fixes it again;
- **Undo** — puts the TV back the way it was before the program's first run.

## What "Speed up" does

| Step | What happens |
|---|---|
| Backup | The original state is saved before any change. Nothing is uninstalled: apps are only turned off. |
| Cleanup | Turns off ads, tracking and preinstalled junk using ready lists for 290+ models ([cleanyourtv](https://github.com/Gathin23/cleanyourtv)). Leaves alone what you use and what you installed yourself. Clears caches, speeds up animations. On weak devices (1.5 GB RAM or less) limits background processes. |
| Menu | A new Apple TV style home screen; the top row holds the apps you use most. The old home screen is turned off only once the new one is seen working — otherwise everything rolls back by itself. |
| Ads | Blocks ads with Private DNS (AdGuard DNS). If it can't be reached from your network, the setting is put back. |
| Wi-Fi | Shows signal, channel and band; removes the false "no internet". A device bought in another country may not see 5 GHz networks — on Xiaomi the program changes the Wi-Fi region, but only when that actually helps. |
| Remote keys | Netflix → YouTube (or SmartTube if you installed it). Prime Video → rus tv on a Russian TV (the latest version is installed for you), otherwise the app you pick. No root. |
| Screen | Clock screensaver after 2 minutes, sleep after 5, against burn-in. Video playback is not interrupted. |
| Security check | Known TV-box malware ([Dr.Web](https://github.com/DoctorWebLtd/malware-iocs)), apps from outside Play Store, risky permissions, microphone and viewing tracking. It only looks, it changes nothing. |
| Report | Free memory and running apps before → after, what was turned off — made for a screenshot. |

Everything is shown in the TV's language: Russian if the TV is in Russian, otherwise English.

## How to use

1. Download the program for your device (Releases):
   - **Windows** — `TV-Acceleration-Windows.zip`, containing `TV Acceleration.exe` (built automatically, not yet tested on Windows).
     On first run Windows may warn you: "More info → Run anyway".
   - **Mac** — `TV-Acceleration-Mac.zip`, containing `TV Acceleration.app`.
     On first run: right-click → Open → Open.
   - **Android phone** (no computer needed) — `TV-Acceleration-Phone.apk`.
2. The TV and the computer (or phone) must be on the same Wi-Fi.
3. Turn on debugging on the TV — the program walks you through it with pictures:
   Settings → Device Preferences → About → press "Build" 7 times → back → Developer options → turn on "USB debugging".
4. Press "Find the TV". The TV asks "Allow debugging?" — tick "Always allow" and press OK.
5. Press "Speed up" and wait 3–4 minutes. The TV restarts once, to check that everything comes up.

The tool that talks to the TV (adb) is downloaded from Google on first run.

## Compatibility

| Device | Status |
|---|---|
| Xiaomi Mi TV Stick (MiTV-AESP0), Android TV 9 | ✅ Tested |
| Other Android TV and Google TV on Android 9–12 (Xiaomi Mi Box, Chromecast with Google TV, Sony, Philips, TCL, Hisense, …) | 🟡 Should work |
| Android TV 13 and later | 🟡 Should work, except remapping the Prime key |
| Android TV 8 and earlier | 🟡 Should work, except ad blocking (no Private DNS) |
| Amazon Fire TV (Fire OS) | 🟠 Partly: cleanup, Wi-Fi, security check; Fire OS does not let the home screen be replaced |
| Samsung (Tizen), LG (webOS), Roku, Apple TV | ❌ Not supported — not Android |

On Google TV the stock home screen is needed by the system (some devices hang at boot without it), so the program
never turns it off; if that keeps the new menu from becoming Home, the install rolls itself back.

## Safety

- The original state is saved before the first change; "Undo" returns exactly that.
- Apps are only turned off (`pm disable-user`), never uninstalled — except the program's own menu.
- Never touched: system UI, settings, Google services and Play Store, keyboard, remote, Bluetooth, HDMI inputs, the maker's boot services.
- Every risky step (menu, DNS, Wi-Fi region) is checked right away and rolled back if it fails.

## For developers

```
python3 -m tvaccel accelerate   # Speed up
python3 -m tvaccel repeat       # Repeat after an update
python3 -m tvaccel restore      # Undo
python3 -m tvaccel info         # just show the device
python3 app.py                  # the window
```

Only Python 3.9+ is needed (no third-party packages). The TV menu is `launcher/` (`sh launcher/build.sh`), the phone
app is `phone/` (Gradle + Chaquopy). GitHub Actions builds the Windows, Mac and phone versions
(`.github/workflows/build.yml`).

## Credits

- The home screen (`launcher/`) is based on [tv-detox](https://github.com/Ansub/tv-detox) by Ansub Khan, MIT —
  see [`launcher/LICENSE-tv-detox`](launcher/LICENSE-tv-detox). Taken at commit `e94a2de`, restyled after Apple TV.
- Per-model cleanup lists (`tvaccel/data/cleanyourtv/`) come from [cleanyourtv](https://github.com/Gathin23/cleanyourtv)
  by Gathin, MIT — see [`tvaccel/data/cleanyourtv/LICENSE`](tvaccel/data/cleanyourtv/LICENSE). Commit `a732cd5`.
- The microphone and viewing-tracking check (`tvaccel/security.py`) follows `tools/privacy.py` from cleanyourtv (MIT).
- Known-malware indicators are downloaded at check time from [Doctor Web malware-iocs](https://github.com/DoctorWebLtd/malware-iocs);
  they are not copied into this repository.
- Phone-to-TV connection: [libadb-android](https://github.com/MuntashirAkon/libadb-android) (Apache-2.0);
  Python on the phone: [Chaquopy](https://chaquo.com/chaquopy/) (MIT); certificate: [Bouncy Castle](https://www.bouncycastle.org/) (MIT).
- Wi-Fi region on the Mi TV Stick: [tweakradje](https://sites.google.com/site/tweakradje/devices/xiaomi-mi-tv-stick).
