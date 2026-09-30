"""SQLite 数据库：每个用户一行，用「清单码」识别，不需要注册。

users 表里存：
  list_json        当前购物清单
  essentials_json  每周必需品（带两家各自选定的商品 ID，下周一键载入、每周检查特价）
  email / notify   特价提醒邮件设置
  coles_store      选择的 Coles 门店 {"id", "name"}（空 = 网上默认价）
  picks_json       选品记忆：{商品名或搜索词: {"coles": {"id","name","override"}, "woolworths": {...}}}
                   你在「换一个」里挑过的商品，下次添加同名商品时自动选中
"""
import json
import re
import secrets
import sqlite3
import threading
import time

from stores import DATA_DIR

DB_PATH = DATA_DIR / "app.db"
MAX_JSON = 200_000  # 单个清单的最大字节数，防止滥用
CODE_RE = re.compile(r"^[A-HJ-NP-Z2-9]{8}$")
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 去掉容易看错的 0/O/1/I

_lock = threading.Lock()
_conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
_conn.row_factory = sqlite3.Row
_conn.executescript("""
CREATE TABLE IF NOT EXISTS users (
    code            TEXT PRIMARY KEY,
    created_at      INTEGER NOT NULL,
    updated_at      INTEGER NOT NULL,
    lang            TEXT NOT NULL DEFAULT 'zh',
    email           TEXT NOT NULL DEFAULT '',
    notify          INTEGER NOT NULL DEFAULT 0,
    list_json       TEXT NOT NULL DEFAULT '[]',
    essentials_json TEXT NOT NULL DEFAULT '[]',
    notified_week   TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
""")
# 给旧数据库补上后来新增的列
_cols = {r["name"] for r in _conn.execute("PRAGMA table_info(users)")}
if "coles_store" not in _cols:
    _conn.execute("ALTER TABLE users ADD COLUMN coles_store TEXT NOT NULL DEFAULT ''")
if "picks_json" not in _cols:
    _conn.execute("ALTER TABLE users ADD COLUMN picks_json TEXT NOT NULL DEFAULT '{}'")
_conn.commit()


def valid_code(code):
    return bool(CODE_RE.match(code or ""))


def create_user(lang="zh"):
    now = int(time.time())
    with _lock:
        while True:
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))
            try:
                _conn.execute("INSERT INTO users (code, created_at, updated_at, lang) VALUES (?, ?, ?, ?)",
                              (code, now, now, lang if lang in ("zh", "en") else "zh"))
                _conn.commit()
                return code
            except sqlite3.IntegrityError:
                continue


def _row_to_user(row):
    return {
        "code": row["code"],
        "lang": row["lang"],
        "email": row["email"],
        "notify": bool(row["notify"]),
        "colesStore": json.loads(row["coles_store"]) if row["coles_store"] else None,
        "list": json.loads(row["list_json"]),
        "essentials": json.loads(row["essentials_json"]),
        "picks": json.loads(row["picks_json"]),
        "notifiedWeek": row["notified_week"],
    }


def get_user(code):
    with _lock:
        row = _conn.execute("SELECT * FROM users WHERE code = ?", (code,)).fetchone()
    return _row_to_user(row) if row else None


def all_users_with_essentials():
    with _lock:
        rows = _conn.execute("SELECT * FROM users WHERE essentials_json != '[]'").fetchall()
    return [_row_to_user(r) for r in rows]


def all_users_with_items():
    """有清单或有每周必需品的用户（这些人的「已选择货品」需要每周更新价格）。"""
    with _lock:
        rows = _conn.execute("SELECT * FROM users WHERE essentials_json != '[]' OR list_json != '[]'").fetchall()
    return [_row_to_user(r) for r in rows]


def _update(code, **cols):
    cols["updated_at"] = int(time.time())
    sets = ", ".join(f"{k} = ?" for k in cols)
    with _lock:
        cur = _conn.execute(f"UPDATE users SET {sets} WHERE code = ?", (*cols.values(), code))
        _conn.commit()
    return cur.rowcount > 0


def _dump(value):
    s = json.dumps(value, ensure_ascii=False)
    if len(s.encode()) > MAX_JSON:
        raise ValueError("too large")
    return s


def save_list(code, items):
    if not isinstance(items, list):
        raise ValueError("list expected")
    return _update(code, list_json=_dump(items))


def save_essentials(code, items):
    if not isinstance(items, list):
        raise ValueError("list expected")
    return _update(code, essentials_json=_dump(items))


def save_picks(code, picks):
    if not isinstance(picks, dict):
        raise ValueError("object expected")
    return _update(code, picks_json=_dump(picks))


def save_settings(code, lang=None, email=None, notify=None, coles_store=False):
    """coles_store: False = 不修改，None = 恢复网上默认价，{"id", "name"} = 选择门店。"""
    cols = {}
    if coles_store is None:
        cols["coles_store"] = ""
    elif coles_store is not False:
        sid, name = str(coles_store.get("id", "")), str(coles_store.get("name", ""))[:100]
        if not sid.isdigit() or len(sid) > 6:
            raise ValueError("invalid store")
        cols["coles_store"] = json.dumps({"id": sid, "name": name}, ensure_ascii=False)
    if lang in ("zh", "en"):
        cols["lang"] = lang
    if email is not None:
        email = email.strip()[:200]
        if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            raise ValueError("invalid email")
        cols["email"] = email
    if notify is not None:
        cols["notify"] = 1 if notify else 0
    return _update(code, **cols) if cols else True


def mark_notified(code, week):
    _update(code, notified_week=week)


def meta_get(key, default=None):
    with _lock:
        row = _conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def meta_set(key, value):
    with _lock:
        _conn.execute("INSERT INTO meta (key, value) VALUES (?, ?) "
                      "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
        _conn.commit()
