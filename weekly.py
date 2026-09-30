"""每周价格更新 + 特价提醒。

澳洲两大超市的价格和特价每周三更新（周三到下周二）。后台线程在每周三 7:00（悉尼时间）：
  1. 慢慢重新查所有用户「每周必需品」的价格（每次请求间隔几秒，被拦截就暂停一会儿）；
  2. 有特价的话给开启了提醒的用户发邮件；
  3. 再慢慢把上周其他被搜过的商品也重新查一遍，存进缓存（见 pricecache.py），保持一周。
用户打开网页时也能在「本周特价」页看到同样的结果。

邮件需要配置环境变量（不配置就只在网页里提醒）：
  SMTP_HOST  SMTP_PORT(默认 587)  SMTP_USER  SMTP_PASS  SMTP_FROM(默认同 SMTP_USER)
  APP_URL    邮件里的链接，例如 https://your-app.zeabur.app
"""
import datetime
import html
import os
import smtplib
import threading
import time
import traceback
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

import db
import pricecache
import stores

SYDNEY = ZoneInfo("Australia/Sydney")
# 慢慢抓：每次请求之间的间隔（秒）；被拦截后暂停多久再继续
PACE = {"coles": 5.0, "woolworths": 2.0}
BLOCKED_PAUSE = 15 * 60
# 每周更新哪些价格：
#   selected（默认，适合本地使用）：只更新「已选择的货品」= 每个用户当前清单里的商品 + 每周必需品。
#       新的一周第一次打开时，别的搜索词不会被重新查，用到才查。
#   all（Docker 镜像里默认，适合多人使用的服务器）：再把过去三周被搜过的所有词也慢慢重新查一遍。
REFRESH_MODE = os.environ.get("WEEKLY_REFRESH", "selected").strip().lower()
MAX_BLOCKS = 3            # 同一轮里被拦截超过这么多次，就跳过这家剩下的，稍后再补
RETRY_AFTER = 60 * 60     # 没更新完的，1 小时后再补跑一轮
STORE_NAMES = {"coles": "Coles", "woolworths": "Woolworths"}


def store_id(user):
    return (user.get("colesStore") or {}).get("id")


def email_enabled():
    return bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USER"))


def week_start(now=None):
    """本价格周的开始日（最近一个周三；周三 7:00 前还算上一周）。"""
    return pricecache.week_start(now).date()


def is_special(p):
    return bool(p and (p.get("was") or p.get("promo") or p.get("multibuy")))


def line_cost(p, qty):
    if not p or p.get("price") is None:
        return None
    mb = p.get("multibuy")
    if mb and qty >= mb["minQty"]:
        bundles = qty // mb["minQty"]
        return bundles * mb["minQty"] * mb["each"] + (qty - bundles * mb["minQty"]) * p["price"]
    return p["price"] * qty


def check_essentials(essentials, coles_store_id=None):
    """查每件必需品在两家的最新价格。返回每件的两家商品 + 是否特价 + 哪家便宜。"""
    out = []
    for e in essentials:
        qty = max(1, int(e.get("qty") or 1))
        row = {"key": e.get("key"), "label": e.get("label"), "qty": qty}
        for store in ("coles", "woolworths"):
            pick = (e.get("picks") or {}).get(store) or {}
            p, err = None, None
            if pick.get("id") is not None:
                try:
                    p = stores.find_product(store, pick["id"], [pick.get("override"), e.get("term"), pick.get("name")],
                                            coles_store_id if store == "coles" else None)
                except Exception as ex:  # 网络/被拦截
                    err = str(ex)
            row[store] = {"product": p, "special": is_special(p), "cost": line_cost(p, qty),
                          "missing": p is None and err is None and pick.get("id") is not None, "error": err}
        cc, wc = row["coles"]["cost"], row["woolworths"]["cost"]
        row["cheaper"] = None if cc is None or wc is None or abs(cc - wc) < 0.005 else ("coles" if cc < wc else "woolworths")
        out.append(row)
    return out


# ---------- 邮件 ----------

TEXT = {
    "zh": {
        "subject": "本周特价：你的必需品有 {n} 件在打折（{week}）",
        "intro": "本周（{week} 起）你的每周必需品里有这些在打折：",
        "was": "原价",
        "open": "打开比价工具",
        "footer": "你收到这封邮件是因为在 Coles vs Woolies 比价里开启了每周特价提醒。可以在「本周特价」页关闭。",
    },
    "en": {
        "subject": "Weekly specials: {n} of your essentials on sale ({week})",
        "intro": "These weekly essentials are on special this week (from {week}):",
        "was": "was",
        "open": "Open the price checker",
        "footer": "You get this because weekly special alerts are on in Coles vs Woolies. Turn them off on the Specials page.",
    },
}


def build_email(user, rows, week):
    t = TEXT[user["lang"] if user["lang"] in TEXT else "zh"]
    hits = [(r, s) for r in rows for s in ("coles", "woolworths") if r[s]["special"]]
    if not hits:
        return None
    app_url = os.environ.get("APP_URL", "")
    lines_txt, lines_html = [], []
    for r, s in hits:
        p = r[s]["product"]
        deal = p["multibuy"]["text"] if p.get("multibuy") else ""
        was = f' ({t["was"]} ${p["was"]:.2f})' if p.get("was") else ""
        lines_txt.append(f'- {r["label"]} @ {STORE_NAMES[s]}: {p["name"]} ${p["price"]:.2f}{was} {deal}'.rstrip())
        color = "#e01a22" if s == "coles" else "#178841"
        was_html = '<br><s style="color:#999">$%.2f</s>' % p["was"] if p.get("was") else ""
        deal_html = '<br><span style="color:#c2410c">%s</span>' % html.escape(deal) if deal else ""
        lines_html.append(
            f'<tr><td style="padding:6px 10px"><b>{html.escape(r["label"])}</b><br>'
            f'<span style="color:#666;font-size:13px">{html.escape(p["name"])}</span></td>'
            f'<td style="padding:6px 10px;color:{color};font-weight:600">{STORE_NAMES[s]}</td>'
            f'<td style="padding:6px 10px;text-align:right"><b>${p["price"]:.2f}</b>{was_html}{deal_html}</td></tr>')
    subject = t["subject"].format(n=len({r["key"] for r, _ in hits}), week=week)
    intro = t["intro"].format(week=week)
    link_txt = f'\n\n{t["open"]}: {app_url}' if app_url else ""
    link_html = f'<p><a href="{html.escape(app_url)}">{t["open"]}</a></p>' if app_url else ""
    text = f'{intro}\n\n' + "\n".join(lines_txt) + link_txt + f'\n\n{t["footer"]}'
    body = (f'<div style="font-family:-apple-system,Helvetica,Arial,sans-serif;max-width:600px">'
            f'<p>{html.escape(intro)}</p><table style="border-collapse:collapse;width:100%">{"".join(lines_html)}</table>'
            f'{link_html}<p style="color:#888;font-size:12px">{html.escape(t["footer"])}</p></div>')
    return subject, text, body


def send_email(to, subject, text, body):
    msg = MIMEMultipart("alternative")
    msg["Subject"], msg["To"] = Header(subject, "utf-8"), to
    msg["From"] = os.environ.get("SMTP_FROM") or os.environ["SMTP_USER"]
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(body, "html", "utf-8"))
    port = int(os.environ.get("SMTP_PORT", "587"))
    if port == 465:
        server = smtplib.SMTP_SSL(os.environ["SMTP_HOST"], port, timeout=30)
    else:
        server = smtplib.SMTP(os.environ["SMTP_HOST"], port, timeout=30)
        server.ehlo()
        if server.has_extn("starttls"):
            server.starttls()
            server.ehlo()
    with server:
        if os.environ.get("SMTP_PASS"):
            server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        server.send_message(msg)


# ---------- 每周任务 ----------

def slow_refresh(keys, label):
    """按顺序慢慢重新查价：跳过本周已经查过的；被拦截就暂停 15 分钟再试，
    拦截太多次就先跳过这家超市剩下的（稍后补跑）。返回是否全部更新完。"""
    done = skipped = failed = deferred = 0
    blocks = {"coles": 0, "woolworths": 0}
    for store, store_id, term in keys:
        if pricecache.is_fresh(store, store_id, term):
            skipped += 1
            continue
        if blocks[store] > MAX_BLOCKS:
            deferred += 1
            continue
        while True:
            try:
                stores.refresh(store, term, store_id)
                done += 1
                break
            except Exception as e:
                if "blocked" in str(e).lower():
                    blocks[store] += 1
                    if blocks[store] > MAX_BLOCKS:
                        deferred += 1
                        print(f"[weekly] {label}: {store} keeps blocking, skipping the rest for now", flush=True)
                        break
                    print(f"[weekly] {label}: blocked by {store}, pausing {BLOCKED_PAUSE // 60} min", flush=True)
                    time.sleep(BLOCKED_PAUSE)
                    continue
                failed += 1  # 其他错误（比如网络问题）：这个词这周先跳过，用户搜索时会再实时查
                break
        time.sleep(PACE[store])
    print(f"[weekly] {label}: refreshed {done}, already fresh {skipped}, failed {failed}, deferred {deferred}", flush=True)
    return deferred == 0


def _key(user, store, term):
    return store, store_id(user) if store == "coles" else None, term.strip().lower()


def essential_keys(users):
    """所有用户必需品要查的 (超市, 门店, 搜索词)，去重。"""
    keys = []
    for user in users:
        for e in user["essentials"]:
            for store in ("coles", "woolworths"):
                pick = (e.get("picks") or {}).get(store) or {}
                term = pick.get("override") or e.get("term")
                if term:
                    keys.append(_key(user, store, term))
    return list(dict.fromkeys(keys))


def list_keys(users):
    """所有用户当前清单里的商品要查的 (超市, 门店, 搜索词)，去重。"""
    keys = []
    for user in users:
        for it in user["list"]:
            for store in ("coles", "woolworths"):
                term = (it.get("override") or {}).get(store) or it.get("term")
                if term:
                    keys.append(_key(user, store, term))
    return list(dict.fromkeys(keys))


def run_weekly(force=False):
    week = week_start().isoformat()
    sent = checked = 0
    everyone = db.all_users_with_items()
    users = [u for u in everyone if u["essentials"]]
    # 1. 先慢慢更新必需品的价格（发邮件要用），再更新各人当前清单里的商品
    complete = slow_refresh(essential_keys(everyone), "essentials")
    complete = slow_refresh(list_keys(everyone), "current lists") and complete
    # 2. 检查特价、发提醒邮件
    for user in users:
        checked += 1
        rows = check_essentials(user["essentials"], store_id(user))
        if not (email_enabled() and user["notify"] and user["email"]):
            continue
        if user["notifiedWeek"] == week and not force:
            continue
        mail = build_email(user, rows, week)
        if mail:
            try:
                send_email(user["email"], *mail)
                sent += 1
            except Exception:
                traceback.print_exc()
                continue
        db.mark_notified(user["code"], week)
    print(f"[weekly] {week}: checked {checked} users, sent {sent} emails", flush=True)
    # 3. （WEEKLY_REFRESH=all）再慢慢更新过去几周其他被搜过的商品，让大家这一周打开网页都直接用缓存
    if REFRESH_MODE == "all":
        complete = slow_refresh(pricecache.stale_keys(), "other searches") and complete
    if complete:
        db.meta_set("last_weekly_run", week)  # 全部完成才记录；中途重启会接着更新还没更新的
    else:
        db.meta_set("weekly_retry_at", str(time.time() + RETRY_AFTER))
        print(f"[weekly] {week}: some prices deferred, retrying in {RETRY_AFTER // 60} min", flush=True)
    return complete


def _loop():
    while True:
        try:
            # week_start 在周三 7:00 才切换到新的一周，所以一到时间就会触发
            retry_at = float(db.meta_get("weekly_retry_at") or 0)
            if db.meta_get("last_weekly_run") != week_start().isoformat() and time.time() >= retry_at:
                run_weekly()
        except Exception:
            traceback.print_exc()
        time.sleep(5 * 60)


def start_scheduler():
    threading.Thread(target=_loop, daemon=True, name="weekly-specials").start()
