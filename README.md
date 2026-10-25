# TV Acceleration

Ускорение и чистка Android TV / Google TV одной кнопкой. Работа в процессе: полное описание будет позже.

```
python3 -m tvaccel accelerate   # «Ускорить»
python3 -m tvaccel restore      # «Вернуть как было»
python3 -m tvaccel info         # только показать устройство
```

## Авторство / Credits

- Домашний экран (`launcher/`) основан на [tv-detox](https://github.com/Ansub/tv-detox) от Ansub Khan,
  лицензия MIT — см. [`launcher/LICENSE-tv-detox`](launcher/LICENSE-tv-detox). Взят из коммита `e94a2de`
  и переделан в стиле Apple TV.
- Списки чистки по моделям (`tvaccel/data/cleanyourtv/`) взяты из [cleanyourtv](https://github.com/Gathin23/cleanyourtv)
  от Gathin, лицензия MIT — см. [`tvaccel/data/cleanyourtv/LICENSE`](tvaccel/data/cleanyourtv/LICENSE). Коммит `a732cd5`.
