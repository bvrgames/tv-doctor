"""Before/after report: memory, processes, disabled apps — one page made for a screenshot.

"Before" is measured once, at the very start of the first run, before anything changes
(baseline.json). Devices first run before this existed fall back to original.json, which has
free memory and the disabled apps but no process count. "After" is measured at the end of a run.
"""
from __future__ import annotations

import html
import json
import os
import pathlib
import time
import webbrowser
from typing import Optional

from . import adb
from .backup import Session
from .i18n import lang, tr
from .launcher import OLD_LAUNCHERS

# Friendly names for packages this program commonly turns off: (Russian, English).
NAMES = {
    "com.miui.tv.analytics": ("Аналитика Xiaomi", "Xiaomi analytics"),
    "com.google.android.feedback": ("Отчёты в Google", "Reports to Google"),
    "com.google.android.tv.bugreportsender": ("Отправка отчётов об ошибках", "Bug report sender"),
    "tv.alphonso.alphonso_eula": ("Alphonso — слежка за просмотром", "Alphonso — viewing tracking"),
    "com.mitv.tvhome.michannel": ("Рекламные каналы Xiaomi", "Xiaomi promo channels"),
    "com.mitv.tvhome.atv": ("PatchWall (рекламная оболочка Xiaomi)", "PatchWall (Xiaomi ad home screen)"),
    "com.xm.webcontent": ("Рекламный контент Xiaomi", "Xiaomi promo content"),
    "com.google.android.tvrecommendations": ("Рекомендации на главном экране", "Home screen recommendations"),
    "android.autoinstalls.config.xiaomi.mibox3": ("Автоустановка рекламных приложений", "Auto-install of promoted apps"),
    "android.autoinstalls.config.xioami.mibox3": ("Автоустановка рекламных приложений (дубль)", "Auto-install of promoted apps (duplicate)"),
    "com.xiaomi.android.tvsetup.partnercustomizer": ("Партнёрские приложения Xiaomi", "Xiaomi partner apps"),
    "com.google.android.partnersetup": ("Партнёрская настройка Google", "Google partner setup"),
    "com.xiaomo.tv.milegal": ("Экран соглашений Xiaomi", "Xiaomi terms screen"),
    "com.google.android.play.games": ("Google Play Игры", "Google Play Games"),
    "com.google.android.videos": ("Google Play Фильмы", "Google Play Movies"),
    "com.google.android.youtube.tvmusic": ("YouTube Music", "YouTube Music"),
    "com.google.android.tv": ("Live Channels (нет ТВ-входов)", "Live Channels (no TV inputs)"),
    "com.google.android.onetimeinitializer": ("Разовая настройка Google", "Google one-time setup"),
    "com.android.onetimeinitializer": ("Разовая настройка Android", "Android one-time setup"),
    "com.google.android.syncadapters.contacts": ("Синхронизация контактов", "Contacts sync"),
    "com.google.android.syncadapters.calendar": ("Синхронизация календаря", "Calendar sync"),
    "com.google.android.backuptransport": ("Резервное копирование Google", "Google backup"),
    "com.android.backupconfirm": ("Подтверждение резервного копирования", "Backup confirmation"),
    "com.android.sharedstoragebackup": ("Резервное копирование памяти", "Storage backup"),
    "com.android.wallpaperbackup": ("Резервное копирование обоев", "Wallpaper backup"),
    "com.android.printspooler": ("Печать", "Printing"),
    "com.android.settings.intelligence": ("Поиск по настройкам", "Settings search"),
    "com.android.se": ("Платёжный чип (NFC), которого нет", "Payment chip (NFC) it doesn't have"),
    "com.android.cts.ctsshim": ("Тестовая заглушка", "Test stub"),
    "com.android.cts.priv.ctsshim": ("Тестовая заглушка", "Test stub"),
    "com.google.android.tvlauncher": ("Стандартный домашний экран Google", "Google's stock home screen"),
    "com.ansub.tvhome": ("Домашний экран tv-detox", "tv-detox home screen"),
    "com.netflix.ninja": ("Netflix", "Netflix"),
    "com.amazon.amazonvideo.livingroom": ("Prime Video", "Prime Video"),
}
GROUPS = (
    ("ads", ("Реклама и навязанные приложения", "Ads and pushed apps"), ("autoinstall", "partner", "recommend", "michannel", "tvhome.atv",
                                                "webcontent", "milegal", "play.games", "videos", "tvmusic")),
    ("track", ("Слежка и статистика", "Tracking and analytics"), ("analytics", "feedback", "bugreport", "alphonso", "logkit", "statistic")),
    ("home", ("Старый домашний экран", "Old home screen"), tuple(OLD_LAUNCHERS)),
    ("misc", ("Служебное, не нужное телевизору", "System leftovers a TV doesn't need"), ("",)),
)


def metrics(dev: adb.Device) -> dict:
    mem = {}
    for line in dev.shell("cat /proc/meminfo").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1].isdigit():
            mem[parts[0].rstrip(":")] = int(parts[1]) // 1024
    users = dev.shell("ps -A -o USER").split()
    return {
        "taken_at": time.strftime("%Y-%m-%d %H:%M"),
        "mem_available_mb": mem.get("MemAvailable", mem.get("MemFree")),
        "mem_total_mb": mem.get("MemTotal"),
        "app_processes": sum(u.startswith("u0_a") for u in users),
        "disabled": sorted(dev.packages("-d")),
    }


def baseline_path(session: Session) -> str:
    return os.path.join(session.dir, "baseline.json")


def save_baseline(session: Session, before: dict) -> None:
    os.makedirs(session.dir, exist_ok=True)
    with open(baseline_path(session), "w", encoding="utf-8") as f:
        json.dump(before, f, ensure_ascii=False, indent=1)


def load_baseline(session: Session) -> dict:
    if os.path.exists(baseline_path(session)):
        with open(baseline_path(session), encoding="utf-8") as f:
            return json.load(f)
    orig = session.original()
    return {"taken_at": orig["taken_at"][:16], "mem_available_mb": orig["device"]["ram_available_mb"],
            "mem_total_mb": orig["device"]["ram_total_mb"], "app_processes": None, "disabled": orig["disabled"]}


def _group(pkg: str) -> str:
    for key, _title, words in GROUPS:
        if any(w and (w in pkg) for w in words) or (key == "home" and pkg in OLD_LAUNCHERS):
            return key
    return "misc"


def _num(v: Optional[int], unit: str = "") -> str:
    return "—" if v is None else f"{v}{unit}"


def render(info, before: dict, after: dict, done: list) -> str:
    ours = sorted(set(after["disabled"]) - set(before["disabled"]))
    already = len(before["disabled"])
    groups = {k: [] for k, _t, _w in GROUPS}
    for p in ours:
        groups[_group(p)].append(p)

    mem_b, mem_a = before.get("mem_available_mb"), after.get("mem_available_mb")
    mem_delta = f"+{mem_a - mem_b} " + tr("МБ", "MB") if mem_b is not None and mem_a is not None and mem_a >= mem_b else ""
    pr_b, pr_a = before.get("app_processes"), after.get("app_processes")
    pr_delta = f"−{pr_b - pr_a}" if pr_b is not None and pr_a is not None and pr_a < pr_b else ""

    def stat(title, b, a, delta, unit=""):
        return (f'<div class="stat"><div class="t">{title}</div><div class="v"><span class="b">{_num(b, unit)}</span>'
                f'<span class="arrow">→</span><span class="a">{_num(a, unit)}</span></div>'
                f'<div class="d">{html.escape(delta)}</div></div>')

    cols = []
    for key, title, _w in GROUPS:
        if groups[key]:
            items = "".join(f"<li>{html.escape(tr(*NAMES[p]) if p in NAMES else p)}</li>" for p in groups[key])
            cols.append(f'<div class="group"><h3>{tr(*title)} <span>{len(groups[key])}</span></h3><ul>{items}</ul></div>')
    chips = "".join(f'<span class="chip">✓ {html.escape(d)}</span>' for d in done)
    device = html.escape(f"{info.manufacturer} {info.model}")
    mb = tr(" МБ", " MB")
    taken = html.escape(before["taken_at"])
    foot = tr(f"«До» — {taken}, до первого запуска программы; «после» — сразу после проверочной перезагрузки. "
              "Ничего не удалено: приложения отключены и возвращаются кнопкой «Вернуть как было».",
              f"“Before”: {taken}, before the program's first run; “after”: right after the check restart. "
              "Nothing was uninstalled: apps are turned off and come back with “Undo”.")
    return f"""<!doctype html><html lang="{lang()}"><head><meta charset="utf-8"><title>TV Acceleration — {tr("отчёт", "report")}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#07070a;color:#fff;font-family:-apple-system,"SF Pro Display","Segoe UI",Roboto,Arial,sans-serif;min-height:100vh}}
.page{{max-width:1180px;margin:0 auto;padding:56px 32px 48px;position:relative}}
.glow{{position:fixed;inset:0;pointer-events:none;background:radial-gradient(900px 560px at 18% 0%,rgba(150,60,200,.40),rgba(7,7,10,0) 70%),radial-gradient(800px 520px at 100% 100%,rgba(30,110,190,.28),rgba(7,7,10,0) 70%)}}
.brand{{font-size:15px;letter-spacing:.14em;text-transform:uppercase;opacity:.55}}
h1{{font-size:46px;font-weight:700;letter-spacing:-.02em;margin:10px 0 6px}}
.sub{{font-size:17px;opacity:.6}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:36px 0 28px}}
.stat{{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.08);border-radius:22px;padding:24px 26px}}
.stat .t{{font-size:15px;opacity:.65}}
.stat .v{{display:flex;align-items:baseline;gap:12px;margin-top:12px;white-space:nowrap}}
.stat .b{{font-size:24px;opacity:.45;text-decoration:line-through;text-decoration-thickness:1px}}
.stat .arrow{{opacity:.4;font-size:22px}}
.stat .a{{font-size:44px;font-weight:700;letter-spacing:-.02em}}
.stat .d{{margin-top:6px;font-size:16px;color:#7ee2a8;min-height:20px}}
.groups{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:18px}}
.group{{background:rgba(255,255,255,.05);border-radius:20px;padding:20px 22px}}
.group h3{{font-size:16px;font-weight:600;margin-bottom:12px;display:flex;justify-content:space-between;gap:8px}}
.group h3 span{{opacity:.5;font-weight:500}}
.group li{{list-style:none;font-size:15px;opacity:.8;padding:5px 0;border-top:1px solid rgba(255,255,255,.06)}}
.group li:first-child{{border-top:0}}
.chips{{display:flex;flex-wrap:wrap;gap:10px;margin-top:26px}}
.chip{{background:rgba(255,255,255,.08);border-radius:999px;padding:8px 14px;font-size:14px;opacity:.85}}
.foot{{margin-top:30px;font-size:13px;opacity:.45;line-height:1.6}}
@media (max-width:760px){{.stats{{grid-template-columns:1fr}}h1{{font-size:34px}}.page{{padding:32px 16px}}}}
</style></head><body><div class="glow"></div><div class="page">
<div class="brand">TV Acceleration · {tr("отчёт", "report")}</div>
<h1>{device}</h1>
<div class="sub">Android {html.escape(info.android_version)} · {info.ram_nominal_gb:g} {tr("ГБ памяти", "GB RAM")} · {html.escape(after["taken_at"])}</div>
<div class="stats">
{stat(tr("Свободная память", "Free memory"), mem_b, mem_a, mem_delta, mb)}
{stat(tr("Запущенных приложений", "Apps running"), pr_b, pr_a, pr_delta)}
<div class="stat"><div class="t">{tr("Отключено лишнего", "Turned off")}</div><div class="v"><span class="a">{len(ours)}</span></div>
<div class="d" style="color:rgba(255,255,255,.55)">{tr(f"ещё {already} было отключено раньше", f"{already} more were already off")}</div></div>
</div>
<div class="groups">{"".join(cols)}</div>
<div class="chips">{chips}</div>
<div class="foot">{foot}</div>
</div></body></html>"""


def write(session: Session, before: dict, after: dict, done: list, open_it: bool = True) -> str:
    path = os.path.join(session.dir, "report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(render(session.info, before, after, done))
    if open_it:
        try:
            webbrowser.open(pathlib.Path(path).resolve().as_uri())  # file:///C:/... on Windows too
        except Exception:
            pass
    return path
