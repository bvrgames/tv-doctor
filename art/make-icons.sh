#!/bin/sh
# Makes every icon from icon.svg: Mac (.icns), Windows (.ico), the phone app, the TV menu
# (icon + Android TV banner) and the window's favicon. Needs Google Chrome (renders the SVG) and macOS (sips, iconutil).
set -e
cd "$(dirname "$0")"
ROOT=..
CHROME=${CHROME:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
T=$(mktemp -d)

# render <viewBox> <width> <height> <out.png>
render() {
  sed "s|viewBox=\"0 0 1024 1024\" width=\"1024\" height=\"1024\"|viewBox=\"$1\" width=\"$2\" height=\"$3\"|" icon.svg > "$T/v.svg"
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size="$2,$3" --screenshot="$4" "file://$T/v.svg" 2>/dev/null
}
render "0 0 1024 1024" 1024 1024 "$T/icon.png"
render "-256 -256 1536 1536" 432 432 "$T/adaptive.png"   # Android 8+ masks the edges: the TV sits in the safe middle
render "-398 -60 1820 1024" 640 360 "$T/banner.png"      # Android TV banner, 16:9
size() { sips -z "$1" "$1" "$T/icon.png" --out "$2" >/dev/null; }

# Mac
mkdir -p "$T/icon.iconset"
for s in 16 32 128 256 512; do
  size $s "$T/icon.iconset/icon_${s}x${s}.png"; size $((s * 2)) "$T/icon.iconset/icon_${s}x${s}@2x.png"
done
iconutil -c icns -o icon.icns "$T/icon.iconset"

# Windows: an .ico that holds PNGs
for s in 16 24 32 48 64 128 256; do size $s "$T/w$s.png"; done
python3 - "$T" <<'PY'
import struct, sys
t = sys.argv[1]; sizes = [16, 24, 32, 48, 64, 128, 256]
blobs = [open(f"{t}/w{s}.png", "rb").read() for s in sizes]
out = struct.pack("<HHH", 0, 1, len(sizes)); off = 6 + 16 * len(sizes)
for s, b in zip(sizes, blobs):
    out += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(b), off); off += len(b)
open("icon.ico", "wb").write(out + b"".join(blobs))
PY

# Phone app
R=$ROOT/phone/app/src/main/res
for d in mdpi:48 hdpi:72 xhdpi:96 xxhdpi:144 xxxhdpi:192; do
  mkdir -p "$R/mipmap-${d%%:*}"; size "${d##*:}" "$R/mipmap-${d%%:*}/ic_launcher.png"
done
mkdir -p "$R/drawable-nodpi" "$R/mipmap-anydpi-v26"
cp "$T/adaptive.png" "$R/drawable-nodpi/ic_launcher_full.png"
cat > "$R/mipmap-anydpi-v26/ic_launcher.xml" <<'XML'
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_full" />
    <foreground android:drawable="@android:color/transparent" />
</adaptive-icon>
XML

# TV menu
L=$ROOT/launcher/res
mkdir -p "$L/mipmap-xhdpi" "$L/drawable-xhdpi"
size 96 "$L/mipmap-xhdpi/ic_launcher.png"
cp "$T/banner.png" "$L/drawable-xhdpi/banner.png"

# The window (favicon)
size 192 "$ROOT/tvaccel/web/icon.png"

cp "$T/icon.png" icon.png
rm -rf "$T"
echo "Icons made."
