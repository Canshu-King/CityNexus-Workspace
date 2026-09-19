"""Isolated static server + API proxy for a throwaway CityNexus preview.

Serves a *copy* of the built frontend and forwards /api/* to a backend running
on a non-default port, so nothing in D:\\moodle\\CityNexus is touched and no
default port (8000 / 5173) is taken away from the concurrent Codex session.

usage: python serve_static.py <dist_dir> <api_base> <port>
"""
from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

DIST = os.path.abspath(sys.argv[1])
API = sys.argv[2].rstrip("/")
PORT = int(sys.argv[3])

HOP_BY_HOP = {"host", "content-length", "connection", "transfer-encoding",
              "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers"}


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST, **kwargs)

    def log_message(self, fmt, *args):  # keep the log tidy
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    # ---------------- API proxy ----------------
    def _proxy(self, method: str) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        req = urllib.request.Request(API + self.path, data=body, method=method)
        for key, value in self.headers.items():
            if key.lower() not in HOP_BY_HOP:
                req.add_header(key, value)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                self._relay(resp.status, resp.headers, resp.read())
        except urllib.error.HTTPError as exc:
            self._relay(exc.code, exc.headers, exc.read())
        except Exception as exc:  # noqa: BLE001
            payload = ("proxy error: %s" % exc).encode()
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def _relay(self, status, headers, data: bytes) -> None:
        self.send_response(status)
        for key, value in headers.items():
            if key.lower() not in HOP_BY_HOP:
                self.send_header(key, value)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self._proxy("GET")
        return self._static()

    def do_HEAD(self):
        if self.path.startswith("/api/"):
            return self._proxy("HEAD")
        return self._static(head_only=True)

    def do_POST(self):
        return self._proxy("POST")

    def do_PUT(self):
        return self._proxy("PUT")

    def do_PATCH(self):
        return self._proxy("PATCH")

    def do_DELETE(self):
        return self._proxy("DELETE")

    def do_OPTIONS(self):
        return self._proxy("OPTIONS")

    # ---------------- static + SPA fallback ----------------
    def _static(self, head_only: bool = False):
        target = self.translate_path(self.path)
        if os.path.isdir(target) and os.path.exists(os.path.join(target, "index.html")):
            target = os.path.join(target, "index.html")
        if not os.path.isfile(target):
            self.path = "/index.html"          # SPA router owns /v8/*, /v10/*
        return super().do_GET() if not head_only else super().do_HEAD()


if __name__ == "__main__":
    os.chdir(DIST)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    sys.stderr.write("serving %s at http://127.0.0.1:%d  (api -> %s)\n" % (DIST, PORT, API))
    sys.stderr.flush()
    server.serve_forever()
