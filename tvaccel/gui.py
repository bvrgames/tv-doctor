"""The program's window: a local web page (http://127.0.0.1) with the guide and three buttons.

The page talks to this server; each button runs the same command as the terminal version
in a background thread, and its printed lines are shown on the page. A question the run
asks (the country, when the IP looks like a VPN) is shown on the page and waits for the
answer. The server stops a minute after the page is closed.
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

from . import adb, cli, discover, i18n
from .adb import AdbError
from .backup import Session
from .device import detect

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
IDLE_EXIT_S = 60


class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.session: Optional[Session] = None
        self.busy = False
        self.log: list = []
        self.result: Optional[str] = None   # "ok" | "error"
        self.question: Optional[str] = None
        self.answer: Optional[str] = None
        self.answered = threading.Event()
        self.last_seen = time.time()


STATE = State()


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


def _job(fn):
    with STATE.lock:
        if STATE.busy:
            return False
        STATE.busy, STATE.result, STATE.log = True, None, []

    def run():
        out = _Lines()
        ok = False
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
                ok = fn() in (0, None, True)
        except AdbError as e:
            out.write(i18n.tr("Ошибка: ", "Error: ") + str(e) + "\n")
        except Exception as e:  # never leave the page spinning
            out.write(f"{type(e).__name__}: {e}\n")
        out.write("\n")
        with STATE.lock:
            STATE.busy, STATE.result = False, "ok" if ok else "error"

    threading.Thread(target=run, daemon=True).start()
    return True


def _find(host: Optional[str]):
    dev = discover.find_tv(host or None)
    i18n.set_from_tv(dev)
    STATE.session = Session(dev, detect(dev))
    cli.print_info(STATE.session.info)
    return 0


def _command(name: str):
    def go():
        if STATE.session is None:
            _find(None)
        serial = STATE.session.dev.serial
        if ":" in serial and not adb.wait_online(serial, 60):  # network: reconnect if it dropped
            raise AdbError(i18n.tr("Телевизор пропал из сети. Проверьте, что он включён, и нажмите «Найти телевизор».",
                                   "The TV dropped off the network. Check it is on and press \"Find the TV\"."))
        return {"accelerate": cli.cmd_accelerate, "repeat": cli.cmd_repeat,
                "restore": cli.cmd_restore}[name](STATE.session)
    return go


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
        if path == "/api/find":
            return self._json({"started": _job(lambda: _find(body.get("host")))})
        if path in ("/api/accelerate", "/api/repeat", "/api/restore"):
            return self._json({"started": _job(_command(path.rsplit("/", 1)[1]))})
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


def serve(port: int = 0):
    """Start the window's server in the background; returns (server, url). The phone app uses
    this directly and shows the url in its own WebView."""
    cli.ASK, cli.OPEN_REPORT = _ask, False
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
