"""每周特价提醒。

澳洲两大超市的特价每周三更新（周三到下周二）。后台线程在每周三早上（悉尼时间）
检查所有用户的「每周必需品」，有特价的话给开启了提醒的用户发邮件。
用户打开网页时也能在「本周特价」页即时看到同样的结果。

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
import stores

SYDNEY = ZoneInfo("Australia/Sydney")
RUN_HOUR = 7  # 周三早上 7 点后运行
STORE_NAMES = {"coles": "Coles", "woolworths": "Woolworths"}


def email_enabled():
    return bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USER"))


def week_start(now=None):
    """本特价周的开始日（最近的周三，悉尼时间）。"""
    now = now or datetime.datetime.now(SYDNEY)
    return (now - datetime.timedelta(days=(now.weekday() - 2) % 7)).date()


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


def check_essentials(essentials):
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
                    p = stores.find_product(store, pick["id"], [pick.get("override"), e.get("term"), pick.get("name")])
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

def run_weekly(force=False):
    week = week_start().isoformat()
    sent = checked = 0
    for user in db.all_users_with_essentials():
        checked += 1
        rows = check_essentials(user["essentials"])  # 同时也预热了缓存，用户打开网页会更快
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
    db.meta_set("last_weekly_run", week)
    print(f"[weekly] {week}: checked {checked} users, sent {sent} emails", flush=True)


def _loop():
    while True:
        try:
            now = datetime.datetime.now(SYDNEY)
            week = week_start(now).isoformat()
            due = now.weekday() != 2 or now.hour >= RUN_HOUR  # 周三要等到早上 7 点
            if due and db.meta_get("last_weekly_run") != week:
                run_weekly()
        except Exception:
            traceback.print_exc()
        time.sleep(15 * 60)


def start_scheduler():
    threading.Thread(target=_loop, daemon=True, name="weekly-specials").start()
