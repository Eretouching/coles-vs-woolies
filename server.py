#!/usr/bin/env python3
"""Coles vs Woolworths 比价工具 — 服务器（只用 Python 标准库 + 系统 curl）。

本地运行:  python3 server.py   然后打开 http://localhost:8765
环境变量:  PORT(默认 8765)  HOST(默认 127.0.0.1，容器里设 0.0.0.0)  DATA_DIR(数据库目录)
          SMTP_* / APP_URL 见 weekly.py
"""
import json
import os
import re
import threading
import time
import urllib.parse
from collections import defaultdict, deque
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import datetime

import db
import pricecache
import stores
import weekly

PORT = int(os.environ.get("PORT", "8765"))
HOST = os.environ.get("HOST", "127.0.0.1")
ROOT = Path(__file__).parent / "static"

# 每个 IP 的请求频率限制：(次数, 秒)
LIMITS = {"search": (90, 60), "api": (120, 60), "create": (10, 3600), "email": (3, 3600), "refresh": (30, 3600)}
_hits = defaultdict(deque)
_hits_lock = threading.Lock()


def allowed(ip, kind):
    n, window = LIMITS[kind]
    now = time.time()
    with _hits_lock:
        q = _hits[(ip, kind)]
        while q and q[0] < now - window:
            q.popleft()
        if len(q) >= n:
            return False
        q.append(now)
        return True


USER_ROUTE = re.compile(r"^/api/users/([A-Z0-9]+)(?:/(list|essentials|picks|settings|specials|test-email))?$")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, fmt, *args):
        if "/api/" in str(args[0] if args else ""):
            super().log_message(fmt, *args)

    def log_error(self, fmt, *args):
        pass  # 忽略 favicon 之类的 404

    def end_headers(self):
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    @property
    def ip(self):
        fwd = self.headers.get("X-Forwarded-For")
        return fwd.split(",")[0].strip() if fwd else self.client_address[0]

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > db.MAX_JSON + 1000:
            raise ValueError("too large")
        return json.loads(self.rfile.read(n) or b"{}")

    # ---------- GET ----------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/healthz":
            return self._json(200, {"ok": True})
        if path == "/api/config":
            ws = pricecache.week_start()
            return self._json(200, {"emailEnabled": weekly.email_enabled(), "week": weekly.week_start().isoformat(),
                                    "nextUpdate": (ws + datetime.timedelta(days=7)).isoformat()})
        if path == "/api/search":
            return self._search(urllib.parse.parse_qs(parsed.query))
        if path == "/api/stores":
            return self._stores(urllib.parse.parse_qs(parsed.query))
        m = USER_ROUTE.match(path)
        if m:
            return self._user_get(m.group(1), m.group(2))
        if path.startswith("/api/"):
            return self._json(404, {"error": "not found"})
        return super().do_GET()

    def _search(self, qs):
        if not allowed(self.ip, "search"):
            return self._json(429, {"error": "too many requests"})
        term = (qs.get("q") or [""])[0].strip()[:100]
        store = (qs.get("store") or [""])[0]
        store_id = (qs.get("storeId") or [""])[0]
        if not term or store not in stores.STORES or (store_id and not store_id.isdigit()):
            return self._json(400, {"error": "need q and store=coles|woolworths"})
        try:
            if (qs.get("fresh") or [""])[0] == "1":
                # 用户点了某个货品的「刷新」：实时抓这一个词。限频：每个 IP 每小时 30 次，同一个词 10 分钟内只抓一次
                if not allowed(self.ip, "refresh"):
                    return self._json(429, {"error": "too many refreshes, try again later"})
                items, fetched_at, cooled = stores.search_fresh(store, term, store_id or None)
                return self._json(200, {"store": store, "q": term, "items": items, "fetchedAt": fetched_at, "cooldown": cooled})
            # 平时价格按周缓存：本周查过的直接返回，每周三 7:00 统一更新
            items, fetched_at = stores.search(store, term, store_id or None, with_time=True)
            self._json(200, {"store": store, "q": term, "items": items, "fetchedAt": fetched_at})
        except Exception as e:  # 网络/被拦截等
            self._json(502, {"store": store, "q": term, "error": f"{type(e).__name__}: {e}"})

    def _stores(self, qs):
        if not allowed(self.ip, "search"):
            return self._json(429, {"error": "too many requests"})
        q = (qs.get("q") or [""])[0].strip()[:40]
        if not q:
            return self._json(400, {"error": "need q (postcode or suburb)"})
        try:
            self._json(200, {"q": q, "coles": stores.nearby_coles_stores(q)})
        except Exception as e:
            self._json(502, {"q": q, "error": f"{type(e).__name__}: {e}"})

    def _user_get(self, code, sub):
        if not allowed(self.ip, "api"):
            return self._json(429, {"error": "too many requests"})
        user = db.get_user(code) if db.valid_code(code) else None
        if not user:
            return self._json(404, {"error": "unknown code"})
        if sub is None:
            return self._json(200, user)
        if sub == "specials":
            rows = weekly.check_essentials(user["essentials"], weekly.store_id(user))
            return self._json(200, {"week": weekly.week_start().isoformat(), "items": rows})
        self._json(405, {"error": "method not allowed"})

    # ---------- POST / PUT ----------
    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/users":
            if not allowed(self.ip, "create"):
                return self._json(429, {"error": "too many requests"})
            try:
                lang = self._body().get("lang")
            except ValueError:
                lang = None
            return self._json(201, {"code": db.create_user(lang or "zh")})
        m = USER_ROUTE.match(path)
        if m and m.group(2) == "test-email":
            return self._test_email(m.group(1))
        self._json(404, {"error": "not found"})

    def do_PUT(self):
        m = USER_ROUTE.match(urllib.parse.urlparse(self.path).path)
        if not m or m.group(2) not in ("list", "essentials", "picks", "settings"):
            return self._json(404, {"error": "not found"})
        if not allowed(self.ip, "api"):
            return self._json(429, {"error": "too many requests"})
        code, sub = m.groups()
        if not db.valid_code(code):
            return self._json(404, {"error": "unknown code"})
        try:
            body = self._body()
            if sub == "list":
                ok = db.save_list(code, body.get("items"))
            elif sub == "essentials":
                ok = db.save_essentials(code, body.get("items"))
            elif sub == "picks":
                ok = db.save_picks(code, body.get("picks"))
            else:
                ok = db.save_settings(code, lang=body.get("lang"), email=body.get("email"), notify=body.get("notify"),
                                      coles_store=body["colesStore"] if "colesStore" in body else False)
        except (ValueError, AttributeError) as e:
            return self._json(400, {"error": str(e)})
        self._json(200 if ok else 404, {"ok": ok})

    def _test_email(self, code):
        if not allowed(self.ip, "email"):
            return self._json(429, {"error": "too many requests"})
        user = db.get_user(code) if db.valid_code(code) else None
        if not user or not user["email"]:
            return self._json(400, {"error": "no email set"})
        if not weekly.email_enabled():
            return self._json(400, {"error": "email not configured on server"})
        rows = weekly.check_essentials(user["essentials"], weekly.store_id(user))
        mail = weekly.build_email(user, rows, weekly.week_start().isoformat())
        if not mail:
            return self._json(200, {"sent": False, "reason": "no specials"})
        try:
            weekly.send_email(user["email"], *mail)
        except Exception as e:
            return self._json(502, {"error": f"{type(e).__name__}: {e}"})
        self._json(200, {"sent": True})


if __name__ == "__main__":
    try:
        httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError:
        print(f"端口 {PORT} 已被占用 —— 比价工具可能已经在运行了，直接打开 http://localhost:{PORT} 即可。")
        print(f"如需重启，先关掉旧的：lsof -ti :{PORT} | xargs kill")
        raise SystemExit(1)
    if HOST != "127.0.0.1" and not os.path.ismount(str(stores.DATA_DIR)):
        print(f"⚠️  数据目录 {stores.DATA_DIR} 不是挂载的存储卷：重新部署或重启后数据库会被清空！"
              f"请在部署平台上把它挂载为持久化存储。", flush=True)
    weekly.start_scheduler()
    print(f"Coles vs Woolworths 比价工具已启动 → http://localhost:{PORT}  （按 Ctrl+C 停止）", flush=True)
    httpd.serve_forever()
