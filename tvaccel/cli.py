"""TV Acceleration command line.

    python3 -m tvaccel accelerate [--host IP]   «Ускорить»
    python3 -m tvaccel repeat     [--host IP]   «Повторить после обновления»
    python3 -m tvaccel restore    [--host IP]   «Вернуть как было»
    python3 -m tvaccel info       [--host IP]   only show the device
"""
from __future__ import annotations

import argparse
import sys

from . import cleanup, discover, dns, i18n, launcher, remote, repeat, report, screensaver, security, wifi
from .adb import AdbError
from .backup import Session
from .device import DeviceInfo, detect
from .i18n import tr
from .keepawake import KeepAwake

# The window (gui.py) replaces these: questions go to the page, the report opens from a button.
ASK = input
OPEN_REPORT = True


def print_info(info: DeviceInfo) -> None:
    mb, gb = tr("МБ", "MB"), tr("ГБ", "GB")
    print(tr("  Устройство:     ", "  Device:         ") + f"{info.manufacturer} {info.model} ({info.device})")
    print(f"  Android:        {info.android_version} (SDK {info.sdk})")
    print(tr("  Прошивка:       ", "  Firmware:       ") + info.build)
    print(tr("  Память:         ", "  Memory:         ") + f"{info.ram_total_mb} {mb} (≈ {info.ram_nominal_gb:g} {gb}), "
          + tr("свободно", "free") + f" {info.ram_available_mb} {mb}")
    if not info.is_tv:
        print(tr("  ВНИМАНИЕ: это не Android TV — устройство не поддерживается.",
                 "  WARNING: this is not an Android TV — the device is not supported."))


def print_security(s: dict) -> None:
    print(tr("  Проверка безопасности (только смотрит, ничего не меняет):",
             "  Security check (only looks, changes nothing):"))
    if s.get("ioc_families"):
        verdict = tr("НАЙДЕНО", "FOUND") if s["malware"] else tr("не найдено", "none found")
        n = s["ioc_families"]
        print(tr(f"    Известные вирусы для Android (Dr.Web, {n} семейств, в т.ч. Vo1d и Pandora для ТВ-приставок): ",
                 f"    Known Android malware (Dr.Web, {n} families incl. Vo1d and Pandora for TV boxes): ") + verdict)
    for line in s["malware"]:
        print(f"      ⚠ {line}")
    firmware = (tr("признаки взлома: ", "signs of tampering: ") + "; ".join(s["firmware"])) if s["firmware"] \
        else tr("признаков взлома нет", "no signs of tampering")
    print(tr("    Прошивка: ", "    Firmware: ") + firmware)
    sections = (("not_from_play", tr("Установлено не из Play Маркета", "Installed from outside Play Store")),
                ("risky", tr("Приложения с опасными правами", "Apps with risky access")),
                ("voice", tr("Голосовые помощники (микрофон)", "Voice assistants (microphone)")),
                ("acr", tr("Слежка за просмотром (ACR)", "Viewing tracking (ACR)")),
                ("telemetry", tr("Сбор статистики", "Analytics")))
    for key, title in sections:
        items = s.get(key) or []
        print(f"    {title}: " + ("" if items else tr("нет", "none")))
        for line in items:
            print(f"      - {line}")
    if s["mic_used"]:
        print(tr("    Недавно обращались к микрофону: ", "    Recently used the microphone: ")
              + ", ".join(sorted(set(s["mic_used"]))))
    for note in s["notes"]:
        print(tr("    ВНИМАНИЕ: ", "    WARNING: ") + note)


def cmd_info(session: Session) -> int:
    print_info(session.info)
    return 0


def warn(text: str) -> None:
    print(tr("  ВНИМАНИЕ: ", "  WARNING: ") + text)


def cmd_accelerate(session: Session, show_info: bool = True) -> int:
    with KeepAwake(session):  # no screensaver or sleep mid-run (see keepawake.py)
        return _accelerate(session, show_info)


def _accelerate(session: Session, show_info: bool = True) -> int:
    if not session.info.is_tv:
        print_info(session.info)
        print(tr("Это не Android TV. Ничего не изменено.", "This is not an Android TV. Nothing was changed."))
        return 1
    first = not session.has_original()
    if first:
        report.save_baseline(session, report.metrics(session.dev))  # the real "before", untouched
    path = session.backup()
    done = []
    if show_info:
        print_info(session.info)
    print(tr("  Резервная копия: ", "  Backup: ") + path)
    if first:
        print(tr("  Это первый запуск — исходное состояние сохранено для «Вернуть как было».",
                 "  First run — the original state is saved for \"Undo\"."))

    print(tr("  Чистка…", "  Cleanup…"))
    c = cleanup.run(session)
    print(tr("  Список: ", "  List: ") + c["source"])
    print(tr(f"  Отключено сейчас: {len(c['disabled_now'])}, уже было отключено: {len(c['already'])}",
             f"  Turned off now: {len(c['disabled_now'])}, already off: {len(c['already'])}"))
    for pkg in c["disabled_now"]:
        print(f"    - {pkg}")
    if c["protected"]:
        print(tr("  Не тронуто (белый список): ", "  Left alone (never-touch list): ") + ", ".join(c["protected"]))
    if c["in_use"]:
        print(tr("  Не тронуто (вы этим пользуетесь): ", "  Left alone (you use these): ") + ", ".join(c["in_use"]))
    if c["cache_freed_mb"] is not None:
        freed = max(c["cache_freed_mb"], 0)
        print(tr(f"  Кэш очищен: освобождено {freed} МБ", f"  Cache cleared: {freed} MB freed"))
    print(tr(f"  Анимации: ускорены (×{c['animation_scale']})", f"  Animations: faster (×{c['animation_scale']})"))
    done += [tr("Кэш очищен", "Cache cleared"), tr("Анимации ускорены", "Faster animations")]
    gb, limit = f"{c['ram_gb']:g}", cleanup.LOW_RAM_GB
    if c["bg_limit"]:
        print(tr(f"  Ограничение фоновых процессов: ВКЛЮЧЕНО (память {gb} ГБ ≤ {limit} ГБ, "
                 f"не больше {cleanup.MAX_CACHED_PROCESSES})",
                 f"  Background process limit: ON ({gb} GB RAM ≤ {limit} GB, "
                 f"at most {cleanup.MAX_CACHED_PROCESSES})"))
        done.append(tr("Фоновые процессы ограничены", "Background processes limited"))
    else:
        print(tr(f"  Ограничение фоновых процессов: не применялось (память {gb} ГБ > {limit} ГБ)",
                 f"  Background process limit: not applied ({gb} GB RAM > {limit} GB)"))

    print("  Wi-Fi…")
    w = wifi.run(session, ask=ASK)
    c = w["connection"]
    if c:
        band = tr("5 ГГц", "5 GHz") if c["freq"] >= 5000 else tr("2,4 ГГц", "2.4 GHz")
        q = wifi.signal_quality(c["rssi"])
        print(tr(f"  Сеть: {c['ssid']}, {band}, канал {c['channel']}, сигнал {c['rssi']} дБм ({q}), "
                 f"скорость {c['speed']} Мбит/с",
                 f"  Network: {c['ssid']}, {band}, channel {c['channel']}, signal {c['rssi']} dBm ({q}), "
                 f"link {c['speed']} Mbit/s"))
    print(tr("  Ложное «нет интернета»: проверка отключена", "  False \"no internet\": check turned off"))
    if w["region_changed"]:
        old, new = w["region_changed"]
        chans = ", ".join(map(str, w["tv_5ghz"]))
        print(tr(f"  Регион Wi-Fi: {old.upper()} → {new}, теперь видны сети 5 ГГц (каналы {chans}). "
                 "Подключиться к ним можно в настройках Wi-Fi.",
                 f"  Wi-Fi region: {old.upper()} → {new}, 5 GHz networks are now visible (channels {chans}). "
                 "You can join them in Wi-Fi settings."))
        done.append(tr(f"Wi-Fi 5 ГГц включён (регион {new})", f"5 GHz Wi-Fi on (region {new})"))
    elif w.get("region"):
        print(tr(f"  Регион Wi-Fi: {w['region'].upper()}, менять не нужно",
                 f"  Wi-Fi region: {w['region'].upper()}, no change needed"))
    for text in w["warnings"]:
        warn(text)

    print(tr("  Блокировка рекламы…", "  Ad blocking…"))
    d = dns.run(session)
    if d["enabled"]:
        print(tr(f"  Частный DNS: AdGuard ({dns.ADGUARD}), рекламных адресов заблокировано при проверке: "
                 f"{d['blocked']} из {d['probes']}",
                 f"  Private DNS: AdGuard ({dns.ADGUARD}), ad addresses blocked in the check: "
                 f"{d['blocked']} of {d['probes']}"))
        done.append(tr("Реклама блокируется (AdGuard DNS)", "Ads blocked (AdGuard DNS)"))
    for text in d["warnings"]:
        warn(text)

    try:
        menu = launcher.install_menu(session)
    except launcher.MenuError as e:
        print(f"  {e}")
        return 1
    print(tr("  Новое меню установлено и открывается кнопкой «Домой», в том числе после перезагрузки.",
             "  The new menu is installed and Home opens it, also after a restart."))
    done.append(tr("Новое меню", "New menu"))
    for pkg in menu["disabled"]:
        print(tr("  Старый домашний экран отключён: ", "  Old home screen turned off: ") + pkg)

    print(tr("  Кнопки пульта…", "  Remote keys…"))
    k = remote.run(session)
    print(tr("  Кнопка Netflix открывает: ", "  The Netflix key opens: ") + k["netflix"])
    print(tr("  Кнопка Prime Video открывает: ", "  The Prime Video key opens: ") + k["prime"])
    if k.get("rustv"):
        print(f"  {k['rustv']}")
    for text in k["warnings"]:
        warn(text)

    sv = screensaver.run(session)
    what = tr("заставка-часы", "clock screensaver") if sv["clock"] else tr("заставка", "screensaver")
    print(tr(f"  Экран: {what} через {sv['screensaver_min']} мин без нажатий, сон через {sv['sleep_min']} мин "
             "(видео не прерывается)",
             f"  Screen: {what} after {sv['screensaver_min']} min without input, sleep after {sv['sleep_min']} min "
             "(video is not interrupted)"))
    done.append(tr(f"Заставка-часы и сон через {sv['sleep_min']} мин", f"Clock screensaver, sleep after {sv['sleep_min']} min"))

    sec = security.run(session.dev)
    print_security(sec)
    if sec.get("ioc_families") and not sec["malware"]:
        done.append(tr("Вирусов не найдено", "No malware found"))
    out = report.write(session, report.load_baseline(session), report.metrics(session.dev), done,
                       open_it=OPEN_REPORT)
    print(tr("  Отчёт «до/после»: ", "  Before/after report: ") + out)
    return 0


def cmd_repeat(session: Session) -> int:
    if not session.has_original():
        print(tr("  Программа ещё не запускалась на этом ТВ — сначала нажмите «Ускорить».",
                 "  The program has not run on this TV yet — press \"Speed up\" first."))
        return 1
    print_info(session.info)
    print(tr("  Проверяю, что вернулось после обновления…", "  Checking what came back after the update…"))
    before = repeat.check(session)
    repeat.print_check(before)
    print(tr("  Применяю всё заново…", "  Applying everything again…"))
    with KeepAwake(session):
        code = _accelerate(session, show_info=False)
    after = repeat.check(session)
    if repeat.anything(before):
        if repeat.anything(after):
            print(tr("  Не удалось исправить:", "  Could not fix:"))
            repeat.print_check(after)
            return 1
        print(tr("  Всё, что вернулось, снова отключено и настроено.", "  Everything that came back is fixed again."))
    return code


def cmd_restore(session: Session) -> int:
    with KeepAwake(session):
        return _restore(session)


def _restore(session: Session) -> int:
    result = session.restore()
    for line in result["settings"]:
        print(tr("  настройка возвращена: ", "  setting restored: ") + line)
    for pkg in result["enabled"]:
        print(tr("  включено обратно: ", "  turned back on: ") + pkg)
    for pkg in result["disabled"]:
        print(tr("  отключено, как было: ", "  turned off, as it was: ") + pkg)
    for pkg in result["uninstalled"]:
        print(tr("  удалено наше приложение: ", "  removed our app: ") + pkg)
    for err in result["errors"]:
        print(tr("  ОШИБКА: ", "  ERROR: ") + err)
    if any(line.startswith(f"global/{wifi.REGION_KEY} ") for line in result["settings"]):
        print(tr("  Перезапускаю Wi-Fi, чтобы вернулся старый регион…",
                 "  Restarting Wi-Fi so the old region applies…"))
        session.dev = wifi.restart_wifi(session)
    left = session.verify_restored()
    for d in left:
        print(tr("  НЕ СОВПАДАЕТ: ", "  DOES NOT MATCH: ") + d)
    if result["errors"] or left:
        return 1
    print(tr("  Готово: всё как было.", "  Done: everything is as it was."))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="tvaccel", description="TV Acceleration")
    parser.add_argument("command", choices=["accelerate", "repeat", "restore", "info"])
    parser.add_argument("--host", help=tr("IP телевизора (по умолчанию — поиск в сети)",
                                          "TV IP address (default: search the network)"))
    args = parser.parse_args(argv)
    try:
        dev = discover.find_tv(args.host)
        i18n.set_from_tv(dev)
        session = Session(dev, detect(dev))
        commands = {"accelerate": cmd_accelerate, "repeat": cmd_repeat, "restore": cmd_restore, "info": cmd_info}
        return commands[args.command](session)
    except AdbError as e:
        print(tr("Ошибка: ", "Error: ") + str(e), file=sys.stderr)
        return 2


