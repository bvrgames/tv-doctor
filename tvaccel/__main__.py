"""TV Acceleration command line.

    python3 -m tvaccel accelerate [--host IP]   «Ускорить»
    python3 -m tvaccel restore    [--host IP]   «Вернуть как было»
    python3 -m tvaccel info       [--host IP]   only show the device
"""
from __future__ import annotations

import argparse
import sys

from . import cleanup, discover, dns, launcher, remote, screensaver, security, wifi
from .adb import AdbError
from .backup import Session
from .device import DeviceInfo, detect


def print_info(info: DeviceInfo) -> None:
    print(f"  Устройство:     {info.manufacturer} {info.model} ({info.device})")
    print(f"  Android:        {info.android_version} (SDK {info.sdk})")
    print(f"  Прошивка:       {info.build}")
    print(f"  Память:         {info.ram_total_mb} МБ (≈ {info.ram_nominal_gb:g} ГБ), "
          f"свободно {info.ram_available_mb} МБ")
    if not info.is_tv:
        print("  ВНИМАНИЕ: это не Android TV — устройство не поддерживается.")


def print_security(s: dict) -> None:
    print("  Проверка безопасности (только смотрит, ничего не меняет):")
    if s.get("ioc_families"):
        verdict = "НАЙДЕНО" if s["malware"] else "не найдено"
        print(f"    Известные вирусы для Android (Dr.Web, {s['ioc_families']} семейств, в т.ч. Vo1d и Pandora для ТВ-приставок): {verdict}")
    for line in s["malware"]:
        print(f"      ⚠ {line}")
    print(f"    Прошивка: {'признаки взлома: ' + '; '.join(s['firmware']) if s['firmware'] else 'признаков взлома нет'}")
    sections = (("not_from_play", "Установлено не из Play Маркета"),
                ("risky", "Приложения с опасными правами"),
                ("voice", "Голосовые помощники (микрофон)"),
                ("acr", "Слежка за просмотром (ACR)"),
                ("telemetry", "Сбор статистики"))
    for key, title in sections:
        items = s.get(key) or []
        print(f"    {title}: {'нет' if not items else ''}")
        for line in items:
            print(f"      - {line}")
    if s["mic_used"]:
        print(f"    Недавно обращались к микрофону: {', '.join(sorted(set(s['mic_used'])))}")
    for note in s["notes"]:
        print(f"    ВНИМАНИЕ: {note}")


def cmd_info(session: Session) -> int:
    print_info(session.info)
    return 0


def cmd_accelerate(session: Session) -> int:
    if not session.info.is_tv:
        print_info(session.info)
        print("Это не Android TV. Ничего не изменено.")
        return 1
    first = not session.has_original()
    path = session.backup()
    print_info(session.info)
    print(f"  Резервная копия: {path}")
    if first:
        print("  Это первый запуск — исходное состояние сохранено для «Вернуть как было».")
    print("  Чистка…")
    c = cleanup.run(session)
    print(f"  Список: {c['source']}")
    print(f"  Отключено сейчас: {len(c['disabled_now'])}, уже было отключено: {len(c['already'])}")
    for pkg in c["disabled_now"]:
        print(f"    - {pkg}")
    if c["protected"]:
        print(f"  Не тронуто (белый список): {', '.join(c['protected'])}")
    if c["in_use"]:
        print(f"  Не тронуто (вы этим пользуетесь): {', '.join(c['in_use'])}")
    if c["cache_freed_mb"] is not None:
        print(f"  Кэш очищен: освобождено {max(c['cache_freed_mb'], 0)} МБ")
    print(f"  Анимации: ускорены (×{c['animation_scale']})")
    if c["bg_limit"]:
        print(f"  Ограничение фоновых процессов: ВКЛЮЧЕНО (память {c['ram_gb']:g} ГБ ≤ {cleanup.LOW_RAM_GB} ГБ, "
              f"не больше {cleanup.MAX_CACHED_PROCESSES})")
    else:
        print(f"  Ограничение фоновых процессов: не применялось (память {c['ram_gb']:g} ГБ > {cleanup.LOW_RAM_GB} ГБ)")
    print("  Wi-Fi…")
    w = wifi.run(session)
    c = w["connection"]
    if c:
        band = "5 ГГц" if c["freq"] >= 5000 else "2,4 ГГц"
        print(f"  Сеть: {c['ssid']}, {band}, канал {c['channel']}, сигнал {c['rssi']} дБм "
              f"({wifi.signal_quality(c['rssi'])}), скорость {c['speed']} Мбит/с")
    print("  Ложное «нет интернета»: проверка отключена")
    if w["region_changed"]:
        old, new = w["region_changed"]
        print(f"  Регион Wi-Fi: {old.upper()} → {new}, теперь видны сети 5 ГГц "
              f"(каналы {', '.join(map(str, w['tv_5ghz']))}). Подключиться к ним можно в настройках Wi-Fi.")
    elif w.get("region"):
        print(f"  Регион Wi-Fi: {w['region'].upper()}, менять не нужно")
    for warn in w["warnings"]:
        print(f"  ВНИМАНИЕ: {warn}")
    print("  Блокировка рекламы…")
    d = dns.run(session)
    if d["enabled"]:
        print(f"  Частный DNS: AdGuard ({dns.ADGUARD}), рекламных адресов заблокировано при проверке: "
              f"{d['blocked']} из {d['probes']}")
    for warn in d["warnings"]:
        print(f"  ВНИМАНИЕ: {warn}")
    try:
        menu = launcher.install_menu(session)
    except launcher.MenuError as e:
        print(f"  {e}")
        return 1
    print("  Новое меню установлено и открывается кнопкой «Домой», в том числе после перезагрузки.")
    for pkg in menu["disabled"]:
        print(f"  Старый домашний экран отключён: {pkg}")
    print("  Кнопки пульта…")
    k = remote.run(session)
    print(f"  Кнопка Netflix открывает: {k['netflix']}")
    print(f"  Кнопка Prime Video открывает: {k['prime']}")
    if k.get("rustv"):
        print(f"  {k['rustv']}")
    for warn in k["warnings"]:
        print(f"  ВНИМАНИЕ: {warn}")
    sv = screensaver.run(session)
    what = "заставка-часы" if sv["clock"] else "заставка"
    print(f"  Экран: {what} через {sv['screensaver_min']} мин без нажатий, сон через {sv['sleep_min']} мин "
          "(видео не прерывается)")
    print_security(security.run(session.dev))
    return 0


def cmd_restore(session: Session) -> int:
    report = session.restore()
    for line in report["settings"]:
        print(f"  настройка возвращена: {line}")
    for pkg in report["enabled"]:
        print(f"  включено обратно: {pkg}")
    for pkg in report["disabled"]:
        print(f"  отключено, как было: {pkg}")
    for pkg in report["uninstalled"]:
        print(f"  удалено наше приложение: {pkg}")
    for err in report["errors"]:
        print(f"  ОШИБКА: {err}")
    if any(line.startswith(f"global/{wifi.REGION_KEY} ") for line in report["settings"]):
        print("  Перезапускаю Wi-Fi, чтобы вернулся старый регион…")
        session.dev = wifi.restart_wifi(session)
    left = session.verify_restored()
    for d in left:
        print(f"  НЕ СОВПАДАЕТ: {d}")
    if report["errors"] or left:
        return 1
    print("  Готово: всё как было.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="tvaccel", description="TV Acceleration")
    parser.add_argument("command", choices=["accelerate", "restore", "info"])
    parser.add_argument("--host", help="IP телевизора (по умолчанию — поиск в сети)")
    args = parser.parse_args(argv)
    try:
        dev = discover.find_tv(args.host)
        session = Session(dev, detect(dev))
        return {"accelerate": cmd_accelerate, "restore": cmd_restore, "info": cmd_info}[args.command](session)
    except AdbError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
