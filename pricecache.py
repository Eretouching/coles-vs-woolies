"""每周价格缓存。

两家超市的价格每周三更新，所以每条搜索结果（超市 + 门店 + 搜索词）只需要每周查一次：
本周（从最近一个周三 7:00 悉尼时间算起）查过的直接用数据库里的，不再访问超市网站。
每周三 7:00 由 weekly.py 的后台任务慢慢把上周查过的搜索词全部重新查一遍。
"""
import datetime
import json
import sqlite3
import threading
import time
from zoneinfo import ZoneInfo

from stores import DATA_DIR

SYDNEY = ZoneInfo("Australia/Sydney")
UPDATE_WEEKDAY, UPDATE_HOUR = 2, 7  # 周三 7:00
KEEP_DAYS = 21  # 三周没人再搜的词就不再每周更新

_lock = threading.Lock()
_conn = sqlite3.connect(str(DATA_DIR / "app.db"), check_same_thread=False, timeout=30)
_conn.row_factory = sqlite3.Row
_conn.execute("PRAGMA journal_mode=WAL")
_conn.executescript("""
CREATE TABLE IF NOT EXISTS price_cache (
    store       TEXT NOT NULL,
    store_id    TEXT NOT NULL DEFAULT '',
    term        TEXT NOT NULL,
    fetched_at  REAL NOT NULL,
    last_used   REAL NOT NULL,
    items_json  TEXT NOT NULL,
    PRIMARY KEY (store, store_id, term)
);
""")
_conn.commit()


def week_start(now=None):
    """本价格周的开始时间：最近一个周三 7:00（悉尼时间）。周三 7:00 前还算上一周。"""
    now = now or datetime.datetime.now(SYDNEY)
    start = (now - datetime.timedelta(days=(now.weekday() - UPDATE_WEEKDAY) % 7)).replace(
        hour=UPDATE_HOUR, minute=0, second=0, microsecond=0)
    if start > now:
        start -= datetime.timedelta(days=7)
    return start


def _key(store, store_id, term):
    return store, store_id or "", term.strip().lower()


def get(store, store_id, term):
    """本周有效的缓存 → (items, fetched_at)；没有返回 None。"""
    k = _key(store, store_id, term)
    with _lock:
        row = _conn.execute("SELECT items_json, fetched_at FROM price_cache WHERE store=? AND store_id=? AND term=?",
                            k).fetchone()
        if row and row["fetched_at"] >= week_start().timestamp():
            _conn.execute("UPDATE price_cache SET last_used=? WHERE store=? AND store_id=? AND term=?", (time.time(), *k))
            _conn.commit()
            return json.loads(row["items_json"]), row["fetched_at"]
    return None


def put(store, store_id, term, items):
    now = time.time()
    with _lock:
        _conn.execute("INSERT INTO price_cache (store, store_id, term, fetched_at, last_used, items_json) "
                      "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(store, store_id, term) DO UPDATE SET "
                      "fetched_at=excluded.fetched_at, items_json=excluded.items_json",
                      (*_key(store, store_id, term), now, now, json.dumps(items, ensure_ascii=False)))
        _conn.commit()
    return now


def stale_keys():
    """本周还没更新、而且最近三周有人用过的搜索词（每周三要重新查的）。"""
    cutoff = time.time() - KEEP_DAYS * 86400
    with _lock:
        _conn.execute("DELETE FROM price_cache WHERE last_used < ?", (cutoff,))
        _conn.commit()
        rows = _conn.execute("SELECT store, store_id, term FROM price_cache WHERE fetched_at < ? "
                             "ORDER BY last_used DESC", (week_start().timestamp(),)).fetchall()
    return [(r["store"], r["store_id"] or None, r["term"]) for r in rows]


def is_fresh(store, store_id, term):
    k = _key(store, store_id, term)
    with _lock:
        row = _conn.execute("SELECT fetched_at FROM price_cache WHERE store=? AND store_id=? AND term=?", k).fetchone()
    return bool(row and row["fetched_at"] >= week_start().timestamp())
