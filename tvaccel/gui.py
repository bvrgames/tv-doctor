"""The program's window: a local web page (http://127.0.0.1) that leads the person screen by screen.

The page talks to this server. While the person turns on debugging, a watcher looks for the TV
in the background and the page moves on by itself once it answers. Each big button runs the same
command as the terminal version in a background thread; its steps drive the progress bar, and a
failure comes back as a simple kind ("notfound", "unauthorized", ...) the page explains in plain
words. A question the run asks (the country, when the IP looks like a VPN) is shown on the page
and waits for the answer. The server stops a minute after the page is closed.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional

from . import adb, cleanup, cli, discover, i18n
from .adb import AdbError
from .discover import NeedsOk, NotFound
from .backup import Session
from .device import detect

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
IDLE_EXIT_S = 60
ASK_WAIT_S = 300  # how long to wait for OK on "Allow debugging?"


class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.session: Optional[Session] = None
        self.busy = False
        self.log: list = []
        self.result: Optional[str] = None   # "ok" | "error"
        self.job: Optional[str] = None
        self.stage: Optional[dict] = None    # {"n", "total", "text"} of the running job
        self.error: Optional[str] = None     # notfound | unauthorized | offline | nottv | other
        self.detail: Optional[str] = None    # the error itself (shown small, for support)
        self.link = "idle"                   # the watcher: idle | searching | unauthorized | found | failed
        self.looks = 0                       # the watcher's finished rounds
        self.question: Optional[str] = None
        self.answer: Optional[str] = None
        self.answered = threading.Event()
        self.last_seen = time.time()


STATE = State()


class Offline(AdbError):
    pass


def _kind(e: Exception) -> str:
    if isinstance(e, NeedsOk):
        return "unauthorized"
    if isinstance(e, NotFound):
        return "notfound"
    if isinstance(e, Offline):
        return "offline"
    return "other"


class _Lines(io.TextIOBase):
    """stdout replacement: every printed line goes to the page's log."""
    def __init__(self):
        self.buf = ""

    def write(self, s):
        self.buf += s
        while "\n" in self.buf:
            line, self.buf = self.buf.split("\n", 1)
            with STATE.lock:
                STATE.log.append(line)
        return len(s)


def _ask(prompt: str) -> str:
    STATE.answered.clear()
    with STATE.lock:
        STATE.question = prompt.strip()
    STATE.answered.wait()
    with STATE.lock:
        STATE.question = None
        return STATE.answer or ""


def _job(name: str, fn):
    with STATE.lock:
        if STATE.busy:
            return False
        STATE.busy, STATE.result, STATE.log = True, None, []
        STATE.job, STATE.stage, STATE.error, STATE.detail = name, None, None, None
        STATE.link = "idle"  # stops the watcher

    def run():
        out = _Lines()
        ok, kind, detail = False, "other", None
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
                ok = fn() in (0, None, True)
            if not ok and STATE.session and not STATE.session.info.is_tv:
                kind = "nottv"
        except AdbError as e:
            out.write(i18n.tr("Ошибка: ", "Error: ") + str(e) + "\n")
            kind, detail = _kind(e), f"{type(e).__name__}: {e}"
        except Exception as e:  # never leave the page spinning
            out.write(f"{type(e).__name__}: {e}\n")
            detail = f"{type(e).__name__}: {e}"
        out.write("\n")
        with STATE.lock:
            STATE.busy, STATE.result = False, "ok" if ok else "error"
            STATE.error = None if ok else kind
            if not ok:  # without an exception, the last lines say what went wrong
                STATE.detail = detail or " / ".join(l.strip() for l in STATE.log[-4:] if l.strip())

    threading.Thread(target=run, daemon=True).start()
    return True


def _find(host: Optional[str]):
    _connected(discover.find_tv(host or None))
    cli.print_info(STATE.session.info)
    return 0


def _connected(dev) -> None:
    i18n.set_from_tv(dev)
    STATE.session = Session(dev, detect(dev))


def _watch():
    """Look for the TV every few seconds until it answers (or a job starts). The person is
    turning on debugging meanwhile; the page follows STATE.link and moves on by itself.
    "unauthorized" means a TV answered but waits for OK on "Allow debugging?" (on the phone,
    connecting simply waits while that question is on screen). Once the TV has let us in, an
    error is a real failure ("failed"): the page shows it with "Try again" instead of waiting."""
    def still_looking():
        with STATE.lock:
            return STATE.link in ("searching", "unauthorized") and not STATE.busy

    def set_link(value):
        with STATE.lock:
            if STATE.link in ("searching", "unauthorized"):
                STATE.link = value

    def fail(kind, e):
        with STATE.lock:
            STATE.link, STATE.error, STATE.detail = "failed", kind, f"{type(e).__name__}: {e}"

    host = None     # once a TV asks "Allow debugging?", keep asking that one only
    asked_at = 0.0  # when it first asked
    while still_looking():
        dev = None
        try:
            if host:
                hosts = [host]
            elif any(st == "device" for _, st in adb.list_devices()):
                hosts = [None]  # already connected (debugging was on and allowed)
            else:
                hosts = [f"{h}:{discover.ADB_PORT}" for h in discover.scan_subnet()]
            for h in hosts:
                asking = threading.Timer(1.5, set_link, ("unauthorized",))  # slow answer: the question is up
                asking.start()
                try:
                    dev = discover.find_tv(h)
                finally:
                    asking.cancel()
                break
            if not dev:
                set_link("searching")
        except NeedsOk as e:
            host = e.serial or host
            asked_at = asked_at or time.time()
            if time.time() - asked_at > ASK_WAIT_S:  # nobody pressed OK
                return fail("unauthorized", e)
            set_link("unauthorized")
        except Exception as e:  # AdbError, or adb still downloading
            if host:  # the TV asked, so it is there: this is not "not found yet"
                return fail("other", e)
            set_link("searching")
        if dev:
            try:
                _connected(dev)  # the TV let us in: read what it is
            except Exception as e:
                return fail("offline" if isinstance(e, Offline) else "other", e)
            with STATE.lock:
                STATE.link = "found"
            return
        with STATE.lock:
            STATE.looks += 1
        time.sleep(2)


def _start_watch() -> None:
    with STATE.lock:
        if STATE.busy or STATE.link in ("searching", "unauthorized"):
            return
        STATE.link, STATE.error, STATE.detail, STATE.result, STATE.looks = "searching", None, None, None, 0
    threading.Thread(target=_watch, daemon=True).start()


def _command(name: str):
    def go():
        if STATE.session is None:
            _find(None)
        serial = STATE.session.dev.serial
        if ":" in serial and not adb.wait_online(serial, 30) and not _found_again():  # network
            raise Offline(i18n.tr("Телевизор пропал из сети. Проверьте, что он включён, и нажмите «Найти телевизор».",
                                   "The TV dropped off the network. Check it is on and press \"Find the TV\"."))
        return {"accelerate": cli.cmd_accelerate, "repeat": cli.cmd_repeat,
                "restore": cli.cmd_restore}[name](STATE.session)
    return go


def _found_again() -> bool:
    """The TV no longer answers at its address: maybe it (or this device) changed networks and
    it got a new one. Look for it again; carry on only if it is the same TV."""
    try:
        adb.disconnect(STATE.session.dev.serial)
        dev = discover.find_tv(None)
        info = detect(dev)
    except AdbError:
        return False
    if info.device_id != STATE.session.info.device_id:
        return False
    STATE.session = Session(dev, info)
    return True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self):
        STATE.last_seen = time.time()
        path = self.path.split("?", 1)[0]
        if path == "/api/state":
            s = STATE.session
            with STATE.lock:
                self._json({
                    "lang": i18n.lang(),
                    "tv": None if s is None else {"name": f"{s.info.manufacturer} {s.info.model}",
                                                  "android": s.info.android_version, "serial": s.dev.serial,
                                                  "ready": s.has_original()},
                    "phone": adb.ON_ANDROID, "link": STATE.link, "looks": STATE.looks, "job": STATE.job,
                    "stage": STATE.stage, "error": STATE.error, "detail": STATE.detail,
                    "busy": STATE.busy, "result": STATE.result, "log": STATE.log[-400:],
                    "question": STATE.question,
                    "report": bool(s and os.path.exists(os.path.join(s.dir, "report.html"))),
                })
            return
        if path == "/report" and STATE.session:
            with open(os.path.join(STATE.session.dir, "report.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        name = "index.html" if path == "/" else path.lstrip("/")
        full = os.path.normpath(os.path.join(WEB, name))
        if not full.startswith(WEB) or not os.path.isfile(full):
            return self._send(404, b"not found", "text/plain")
        ctype = {"html": "text/html; charset=utf-8", "js": "text/javascript", "css": "text/css",
                 "jpg": "image/jpeg", "png": "image/png", "svg": "image/svg+xml"}.get(full.rsplit(".", 1)[-1],
                                                                                    "application/octet-stream")
        with open(full, "rb") as f:
            self._send(200, f.read(), ctype)

    def do_POST(self):
        STATE.last_seen = time.time()
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length) or b"{}")
        path = self.path.split("?", 1)[0]
        if path == "/api/watch":
            _start_watch()
            return self._json({"ok": True})
        if path == "/api/find":
            return self._json({"started": _job("find", lambda: _find(body.get("host")))})
        if path in ("/api/accelerate", "/api/repeat", "/api/restore"):
            name = path.rsplit("/", 1)[1]
            return self._json({"started": _job(name, _command(name))})
        if path == "/api/lang":  # the window's language: the system's on first load, or the RU / EN switch
            if body.get("choose") in ("ru", "en"):
                i18n.choose(body["choose"])
            else:
                i18n.set_system(str(body.get("system", "")))
            return self._json({"lang": i18n.lang()})
        if path == "/api/answer":
            with STATE.lock:
                STATE.answer = str(body.get("text", ""))
            STATE.answered.set()
            return self._json({"ok": True})
        self._json({"error": "unknown"}, 404)


def _stage(n: int, total: int, text: str) -> None:
    with STATE.lock:
        STATE.stage = {"n": n, "total": total, "text": text}


def serve(port: int = 0):
    """Start the window's server in the background; returns (server, url). The phone app uses
    this directly and shows the url in its own WebView."""
    cli.ASK, cli.OPEN_REPORT = _ask, False
    cli.STAGE = _stage
    cleanup.start_update()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/"


def main(open_browser: bool = True, port: int = 0) -> None:
    server, url = serve(port)
    print(url, flush=True)
    if open_browser:
        webbrowser.open(url)
    while True:  # stop once the page has been closed for a while and nothing runs
        time.sleep(5)
        if not STATE.busy and time.time() - STATE.last_seen > IDLE_EXIT_S:
            server.shutdown()
            return


if __name__ == "__main__":
    main()
