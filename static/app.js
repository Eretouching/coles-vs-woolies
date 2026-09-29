"use strict";

// ================= 文案（中英双语） =================
const I18N = {
  zh: {
    titleSuffix: "比价", subtitle: "输入购物清单（中文或英文都行），实时比较两家超市的价格，告诉你去哪家更省钱。",
    tabList: "购物清单", tabSpecials: "本周特价", add: "添加",
    placeholder: "例如：牛奶 / 香蕉 x3 / a2 milk 2L / Tim Tam",
    autoPick: "自动选品：", modeMatch: "最相关", modeCheap: "单价最便宜",
    refresh: "↻ 刷新价格", clear: "清空清单", newWeek: "⟳ 开始新一周（{n} 件必需品）",
    confirmClear: "确定清空整个购物清单？", confirmNewWeek: "用 {n} 件每周必需品替换当前清单？",
    noEssentials: "还没有每周必需品。点商品名左边的 ☆ 就能加入，下周一键载入。",
    empty: "清单是空的。<br>在上面输入想买的东西，或点一下常用商品快速添加。",
    starOn: "每周必需品（点击取消）", starOff: "设为每周必需品", editTerm: "修改英文搜索词",
    promptTerm: "英文搜索词（两家超市都用英文搜索）：", del: "删除",
    loading: "查询中…", failed: "查询失败：", retry: "重试", notFound: "没有找到，试试换个英文关键词",
    search: "搜索", swap: "换一个", cheaper: "更便宜", same: "同价", outOfStock: "暂时缺货",
    promo_half: "半价", promo_special: "特价",
    multibuyTip: "买 {n} 件每件 {p}",
    allAt: "全在 {s} 买", cheaperCount: "{n} 件更便宜", split: "两家分开买", splitSub: "每件都挑便宜的",
    querying: "正在查询价格…", tie: "两家总价一样 {p}。",
    verdict: "整单去 <b>{s}</b> 更便宜，省 <b>{p}</b>（{pct}%）。",
    splitMore: " 如果两家分开买（每件去便宜的那家），还能再省 {p}。",
    pending: "（还有 {n} 件在查询/未找到，未计入）",
    pkSearch: "换个英文关键词搜索…", pkNone: "没有结果，换个关键词试试", noServer: "无法连接服务器",
    bannerSpecials: "🔥 本周你的必需品有 {n} 件在打折",
    view: "查看",
    spTitle: "本周特价（{d} 起）", spIntro: "两家超市的特价每周三更新。这里检查你标了 ☆ 的每周必需品本周有没有打折。",
    spEmpty: "还没有每周必需品。在「购物清单」里点商品名左边的 ☆ 标记你每周都买的东西。",
    spChecking: "正在检查 {n} 件必需品的本周价格…",
    spHits: "本周 <b>{n}</b> 件必需品在打折，按原价算共省 <b>{p}</b>。",
    spNoHits: "本周你的必需品都没有打折。",
    spCheaperAt: "本周 {s} 更便宜", spMissing: "这周找不到这个商品", notPicked: "未选商品",
    save: "省 {p}", was: "原价 {p}",
    remindTitle: "特价提醒", remindIntro: "每周三早上（悉尼时间）自动检查，你的必需品有特价就发邮件告诉你。",
    email: "邮箱", emailPh: "you@example.com", notifyOn: "开启每周邮件提醒", saveBtn: "保存", testBtn: "现在发一封试试",
    saved: "已保存", sentOk: "已发送，请查收邮件", sentNone: "本周没有特价，没有发送", invalidEmail: "邮箱格式不对",
    emailOff: "服务器还没有配置发信邮箱（SMTP），目前只能在这个页面查看特价。部署时设置 SMTP 环境变量即可开启邮件提醒。",
    codeTitle: "我的清单码", codeIntro: "清单和每周必需品保存在服务器上。在另一台设备（比如手机）输入这个码，就能看到同一份清单。",
    codeSwitch: "切换到这个码", codeBad: "找不到这个清单码", close: "关闭", codeChip: "清单码 {c}",
    footer: "价格来自 coles.com.au 与 woolworths.com.au 网上商城（默认门店），实体店偶尔不同。点「换一个」可以手动挑选两边的同款商品，比较更准。",
  },
  en: {
    titleSuffix: "Price Check", subtitle: "Type your shopping list and compare live prices at both supermarkets to see where it's cheaper.",
    tabList: "Shopping list", tabSpecials: "This week's specials", add: "Add",
    placeholder: "e.g. milk / bananas x3 / a2 milk 2L / 牛奶",
    autoPick: "Auto-pick:", modeMatch: "Most relevant", modeCheap: "Cheapest per unit",
    refresh: "↻ Refresh prices", clear: "Clear list", newWeek: "⟳ New week ({n} essentials)",
    confirmClear: "Clear the whole shopping list?", confirmNewWeek: "Replace the current list with your {n} weekly essentials?",
    noEssentials: "No weekly essentials yet. Tap the ☆ next to an item to add it, then reload them next week in one tap.",
    empty: "Your list is empty.<br>Type something above, or tap a common item to add it.",
    starOn: "Weekly essential (tap to remove)", starOff: "Mark as weekly essential", editTerm: "Edit search term",
    promptTerm: "Search term (both supermarkets search in English):", del: "Remove",
    loading: "Loading…", failed: "Failed: ", retry: "Retry", notFound: "Nothing found, try another keyword",
    search: "Search", swap: "Change", cheaper: "Cheaper", same: "Same price", outOfStock: "Out of stock",
    promo_half: "½ price", promo_special: "Special",
    multibuyTip: "{p} each when you buy {n}",
    allAt: "All at {s}", cheaperCount: "{n} cheaper here", split: "Split across both", splitSub: "each item where cheaper",
    querying: "Checking prices…", tie: "Both come to {p}.",
    verdict: "<b>{s}</b> is cheaper for the whole list, saving <b>{p}</b> ({pct}%).",
    splitMore: " Split the shop across both stores and save another {p}.",
    pending: " ({n} items still loading / not found, not counted)",
    pkSearch: "Search another keyword…", pkNone: "No results, try another keyword", noServer: "Cannot reach the server",
    bannerSpecials: "🔥 Essentials on special this week: {n}",
    view: "View",
    spTitle: "Specials for the week from {d}", spIntro: "Both supermarkets change specials every Wednesday. This checks the ☆ weekly essentials you've marked.",
    spEmpty: "No weekly essentials yet. On the Shopping list, tap the ☆ next to the things you buy every week.",
    spChecking: "Checking this week's prices for {n} essentials…",
    spHits: "Essentials on special this week: <b>{n}</b> · <b>{p}</b> off the regular price.",
    spNoHits: "None of your essentials are on special this week.",
    spCheaperAt: "{s} is cheaper this week", spMissing: "Not found this week", notPicked: "No product picked",
    save: "save {p}", was: "was {p}",
    remindTitle: "Special alerts", remindIntro: "Every Wednesday morning (Sydney time) we check your essentials and email you if any are on special.",
    email: "Email", emailPh: "you@example.com", notifyOn: "Email me weekly specials", saveBtn: "Save", testBtn: "Send one now",
    saved: "Saved", sentOk: "Sent, check your inbox", sentNone: "No specials this week, nothing sent", invalidEmail: "Invalid email address",
    emailOff: "Email (SMTP) isn't set up on this server yet, so specials only show on this page. Set the SMTP environment variables when deploying to turn on email alerts.",
    codeTitle: "My list code", codeIntro: "Your list and weekly essentials are saved on the server. Enter this code on another device (like your phone) to use the same list.",
    codeSwitch: "Switch to this code", codeBad: "Code not found", close: "Close", codeChip: "Code {c}",
    footer: "Prices come from the coles.com.au and woolworths.com.au online stores (default store) and may differ slightly in store. Tap “Change” to pick matching products on both sides for a fairer comparison.",
  },
};
const QUICK = {
  zh: ["牛奶", "鸡蛋", "面包", "香蕉", "大米", "鸡胸肉", "牛肉末", "西红柿", "土豆", "卫生纸", "洗衣液", "洗洁精"],
  en: ["milk", "eggs", "bread", "bananas", "rice", "chicken breast", "beef mince", "tomatoes", "potatoes", "toilet paper", "laundry liquid", "dishwashing liquid"],
};

// ================= 状态 =================
const STORES = ["coles", "woolworths"];
const STORE_NAME = { coles: "Coles", woolworths: "Woolworths" };
const LS = { code: "cvw-code", lang: "cvw-lang", mode: "cvw-mode", legacy: "cvw-state-v1" };

const prefs = {
  lang: lsGet(LS.lang) || ((navigator.language || "").toLowerCase().startsWith("zh") ? "zh" : "en"),
  mode: lsGet(LS.mode) || "cheap",
};
let code = lsGet(LS.code);
let items = [];        // 当前清单 [{id,label,term,qty,sel,override}]
let essentials = [];   // 每周必需品 [{key,label,term,qty,picks:{coles:{id,name,override},woolworths:{...}}}]
let config = { emailEnabled: false, week: "" };
let user = { email: "", notify: false };
let specials = null;   // 本周特价检查结果
let tab = "list";
const results = {};    // itemId -> {coles:{items|error|loading}, woolworths:...}

function lsGet(k) { try { return localStorage.getItem(k); } catch { return null; } }
function lsSet(k, v) { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch {} }

const $ = s => document.querySelector(s);
const money = n => n == null ? "—" : "$" + n.toFixed(2);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const uid = () => Math.random().toString(36).slice(2, 9);
const keyOf = label => label.trim().toLowerCase();

function t(key, vars = {}) {
  const s = (I18N[prefs.lang] || I18N.zh)[key] ?? I18N.zh[key] ?? key;
  return s.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? "");
}

// ================= 服务器 =================
async function api(method, path, body) {
  const res = await fetch(path, {
    method, headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(data.error || res.statusText), { status: res.status });
  return data;
}

let saveTimer = null;
function saveList() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => code && api("PUT", `/api/users/${code}/list`, { items }).catch(() => {}), 600);
}
let essTimer = null;
function saveEssentials() {
  clearTimeout(essTimer);
  essTimer = setTimeout(async () => {
    if (!code) return;
    await api("PUT", `/api/users/${code}/essentials`, { items: essentials }).catch(() => {});
    loadSpecials();  // 必需品变了，重新检查本周特价
  }, 800);
}

async function loadUser(c) {
  const u = await api("GET", `/api/users/${c}`);
  code = c; lsSet(LS.code, c);
  items = u.list || []; essentials = u.essentials || [];
  user = { email: u.email || "", notify: !!u.notify };
  specials = null;
  Object.keys(results).forEach(k => delete results[k]);
  return u;
}

async function initUser() {
  if (code) {
    try { return await loadUser(code); } catch (e) { if (e.status !== 404) throw e; }
  }
  const { code: c } = await api("POST", "/api/users", { lang: prefs.lang });
  await loadUser(c);
  // 把旧版本存在浏览器里的清单迁移到服务器
  try {
    const old = JSON.parse(lsGet(LS.legacy));
    if (old && Array.isArray(old.items) && old.items.length) {
      items = old.items; saveList(); lsSet(LS.legacy, null);
    }
  } catch {}
}

// ================= 商品数据 =================
function toTerm(label) {
  const s = label.trim();
  if (!/[一-鿿]/.test(s)) return s;
  if (DICT[s]) return DICT[s];
  const keys = Object.keys(DICT).filter(k => s.includes(k)).sort((a, b) => b.length - a.length);
  const extra = s.replace(/[一-鿿]+/g, " ").trim();
  // 只保留带字母的补充（如 "2L"、"a2"），纯数字如 "12个" 不影响搜索
  if (keys.length) return (DICT[keys[0]] + (/[a-z]/i.test(extra) ? " " + extra : "")).trim();
  return extra || s;
}

async function fetchStore(item, store, force) {
  const r = results[item.id] ||= {};
  if (r[store] && !force && !r[store].error) return;
  r[store] = { loading: true };
  renderList();
  const q = item.override?.[store] || item.term;
  try {
    const data = await api("GET", `/api/search?store=${store}&q=${encodeURIComponent(q)}`);
    r[store] = { items: data.items };
  } catch (e) {
    r[store] = { error: e.status ? e.message : t("noServer") };
  }
  renderList();
}
function fetchItem(item, force) { STORES.forEach(s => fetchStore(item, s, force)); }

// 当前为某商品在某店选中的产品
function chosen(item, store) {
  const list = results[item.id]?.[store]?.items;
  if (!list || !list.length) return null;
  const pinned = item.sel?.[store];
  if (pinned != null) { const p = list.find(x => String(x.id) === String(pinned)); if (p) return p; }
  const avail = list.filter(p => p.available && p.price != null);
  const pool = avail.length ? avail : list;
  if (prefs.mode === "cheap" && pool[0].unitPrice != null) {
    // 只在前 6 个最相关的结果里挑，且单位要和第一名一致（避免拿冷冻香蕉块去比新鲜香蕉）
    const std = pool[0].unitStd;
    return pool.slice(0, 6).filter(p => p.unitStd === std && p.unitPrice != null)
      .sort((a, b) => a.unitPrice - b.unitPrice)[0];
  }
  return pool[0];
}

// 考虑多买优惠后的小计
function lineCost(p, qty) {
  if (!p || p.price == null) return null;
  const mb = p.multibuy;
  if (mb && qty >= mb.minQty) {
    const bundles = Math.floor(qty / mb.minQty);
    return bundles * mb.minQty * mb.each + (qty - bundles * mb.minQty) * p.price;
  }
  return p.price * qty;
}

// 两边比较：规格不同比单价，否则比小计
function compare(item) {
  const c = chosen(item, "coles"), w = chosen(item, "woolworths");
  const cc = lineCost(c, item.qty), wc = lineCost(w, item.qty);
  if (cc == null || wc == null) return { c, w, cc, wc, winner: null };
  let winner;
  if (c.unitStd && c.unitStd === w.unitStd && c.unitPrice && w.unitPrice && c.size !== w.size) {
    // 单价差 1% 以内算同价（每张纸这类单价很小，不能用固定的 0.5 分钱判断）
    winner = Math.abs(c.unitPrice - w.unitPrice) / Math.max(c.unitPrice, w.unitPrice) < 0.01 ? "tie"
      : c.unitPrice < w.unitPrice ? "coles" : "woolworths";
  } else {
    winner = Math.abs(cc - wc) < 0.005 ? "tie" : cc < wc ? "coles" : "woolworths";
  }
  return { c, w, cc, wc, winner };
}

// ================= 每周必需品 =================
const essentialOf = item => essentials.find(e => e.key === keyOf(item.label));

function essentialFrom(item) {
  const picks = {};
  for (const s of STORES) {
    const p = chosen(item, s);
    picks[s] = p ? { id: p.id, name: p.name, override: item.override?.[s] || null } : null;
  }
  return { key: keyOf(item.label), label: item.label, term: item.term, qty: item.qty, picks };
}

function toggleEssential(item) {
  const e = essentialOf(item);
  essentials = e ? essentials.filter(x => x !== e) : [...essentials, essentialFrom(item)];
  saveEssentials(); render();
}

// 已标记的必需品：换了商品/数量/关键词后同步更新
function syncEssential(item) {
  const e = essentialOf(item);
  if (!e) return;
  const fresh = essentialFrom(item);
  for (const s of STORES) if (!fresh.picks[s]) fresh.picks[s] = e.picks?.[s] || null;  // 还没查到时保留旧的
  essentials = essentials.map(x => x === e ? fresh : x);
  saveEssentials();
}

function startNewWeek() {
  if (!essentials.length) return alert(t("noEssentials"));
  if (items.length && !confirm(t("confirmNewWeek", { n: essentials.length }))) return;
  items = essentials.map(e => ({
    id: uid(), label: e.label, term: e.term, qty: e.qty || 1,
    sel: Object.fromEntries(STORES.map(s => [s, e.picks?.[s]?.id ?? null]).filter(([, v]) => v != null)),
    override: Object.fromEntries(STORES.map(s => [s, e.picks?.[s]?.override]).filter(([, v]) => v)),
  }));
  saveList(); render(); items.forEach(it => fetchItem(it));
}

// ================= 渲染：通用 =================
function applyI18n() {
  document.documentElement.lang = prefs.lang === "zh" ? "zh-CN" : "en";
  document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
  $("#addInput").placeholder = t("placeholder");
  $("#pkSearch").placeholder = t("pkSearch");
  $("#chips").innerHTML = QUICK[prefs.lang].map(q => `<button class="chip" type="button">${esc(q)}</button>`).join("");
  $("#langSeg").querySelectorAll("button").forEach(b => b.classList.toggle("on", b.dataset.lang === prefs.lang));
  $("#codeBtn").textContent = code ? t("codeChip", { c: code }) : "…";
}

function render() {
  document.querySelectorAll(".tabs button").forEach(b => b.classList.toggle("on", b.dataset.tab === tab));
  $("#tab-list").hidden = tab !== "list";
  $("#tab-specials").hidden = tab !== "specials";
  renderList();
  renderSpecials();
}

// ================= 渲染：购物清单 =================
function renderList() {
  $("#modeSeg").querySelectorAll("button").forEach(b => b.classList.toggle("on", b.dataset.mode === prefs.mode));
  const nb = $("#newWeekBtn");
  nb.textContent = t("newWeek", { n: essentials.length });
  nb.hidden = !essentials.length;

  const list = $("#list");
  if (!items.length) {
    list.innerHTML = `<div class="empty">${t("empty")}</div>`;
    $("#summary").innerHTML = "";
    return;
  }
  const cmp = items.map(it => ({ it, ...compare(it) }));
  list.innerHTML = cmp.map(({ it, c, w, cc, wc, winner }) => {
    const star = !!essentialOf(it);
    return `
    <div class="item" data-id="${it.id}">
      <div class="item-head">
        <button class="star ${star ? "on" : ""}" data-act="star" title="${t(star ? "starOn" : "starOff")}">${star ? "★" : "☆"}</button>
        <span class="name">${esc(it.label)}</span>
        ${it.term !== it.label ? `<span class="term" data-act="term" title="${t("editTerm")}">${esc(it.term)}</span>` : ""}
        <span class="spacer"></span>
        <span class="qty"><button data-act="dec">−</button><span>${it.qty}</span><button data-act="inc">+</button></span>
        <button class="ghost" data-act="del" title="${t("del")}">✕</button>
      </div>
      <div class="pair">
        ${side(it, "coles", c, cc, winner)}
        ${side(it, "woolworths", w, wc, winner)}
      </div>
    </div>`;
  }).join("");
  renderSummary(cmp);
  backfillEssentials();
}

function badgesFor(p) {
  return [
    p.promo ? `<span class="badge">${t("promo_" + p.promo)}</span>` : "",
    p.multibuy ? `<span class="badge" title="${esc(t("multibuyTip", { n: p.multibuy.minQty, p: money(p.multibuy.each) }))}">${esc(p.multibuy.text)}</span>` : "",
    !p.available ? `<span class="badge na">${t("outOfStock")}</span>` : "",
  ].join("");
}

function side(it, store, p, cost, winner) {
  const r = results[it.id]?.[store];
  const tag = `<div class="store-tag ${store === "coles" ? "c" : "w"}">${STORE_NAME[store]}</div>`;
  if (!r || r.loading) return `<div class="side"><div class="info">${tag}<div class="msg">${t("loading")}</div></div></div>`;
  if (r.error) return `<div class="side"><div class="info">${tag}<div class="msg err">${t("failed")}${esc(r.error)}</div>
    <button class="ghost" data-act="retry" data-store="${store}">${t("retry")}</button></div></div>`;
  if (!p) return `<div class="side"><div class="info">${tag}<div class="msg">${t("notFound")}</div></div>
    <button class="ghost swap" data-act="pick" data-store="${store}">${t("search")}</button></div>`;
  const isWin = winner === store;
  const badges = (isWin ? `<span class="badge win">${t("cheaper")}</span>` : "")
    + (winner === "tie" ? `<span class="badge">${t("same")}</span>` : "") + badgesFor(p);
  return `<div class="side ${isWin ? "win" : ""}">
    ${p.image ? `<img src="${esc(p.image)}" alt="" loading="lazy">` : ""}
    <div class="info">
      ${tag}
      <div class="pname"><a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.name)}</a></div>
      <div><span class="price">${money(p.price)}</span>${p.was ? `<span class="was">${money(p.was)}</span>` : ""}
        ${it.qty > 1 ? `<span class="unit"> × ${it.qty} = ${money(cost)}</span>` : ""}</div>
      <div class="unit">${esc(p.unitLabel || "")}</div>
      <div class="badges">${badges}</div>
    </div>
    <button class="ghost swap" data-act="pick" data-store="${store}">${t("swap")}</button>
  </div>`;
}

function renderSummary(cmp) {
  let tc = 0, tw = 0, split = 0, ready = 0, winsC = 0, winsW = 0;
  for (const { cc, wc, winner } of cmp) {
    if (cc == null || wc == null) continue;
    ready++; tc += cc; tw += wc; split += Math.min(cc, wc);
    if (winner === "coles") winsC++;
    if (winner === "woolworths") winsW++;
  }
  if (!ready) { $("#summary").innerHTML = `<div class="verdict">${t("querying")}</div>`; return; }
  const best = Math.abs(tc - tw) < 0.005 ? "tie" : tc < tw ? "coles" : "woolworths";
  const diff = Math.abs(tc - tw), splitSave = Math.min(tc, tw) - split;
  let verdict = best === "tie" ? t("tie", { p: money(tc) })
    : t("verdict", { s: STORE_NAME[best], p: money(diff), pct: (diff / Math.max(tc, tw) * 100).toFixed(1) });
  if (splitSave >= 0.5) verdict += t("splitMore", { p: money(splitSave) });
  if (items.length - ready) verdict += t("pending", { n: items.length - ready });
  $("#summary").innerHTML = `
    <div class="summary">
      <div class="tot ${best === "coles" ? "best" : ""}"><div class="lbl"><span class="dot c"></span>${t("allAt", { s: "Coles" })}</div>
        <div class="amt">${money(tc)}</div><div class="sub">${t("cheaperCount", { n: winsC })}</div></div>
      <div class="tot ${best === "woolworths" ? "best" : ""}"><div class="lbl"><span class="dot w"></span>${t("allAt", { s: "Woolworths" })}</div>
        <div class="amt">${money(tw)}</div><div class="sub">${t("cheaperCount", { n: winsW })}</div></div>
      <div class="tot"><div class="lbl">${t("split")}</div>
        <div class="amt">${money(split)}</div><div class="sub">${t("splitSub")}</div></div>
    </div>
    <div class="verdict">${verdict}</div>`;
}

// 标了必需品但当时还没查到价格的，查到后补记商品
function backfillEssentials() {
  for (const it of items) {
    const e = essentialOf(it);
    if (e && STORES.some(s => !e.picks?.[s] && chosen(it, s))) syncEssential(it);
  }
}

// ================= 本周特价 =================
let specialsLoading = false;
async function loadSpecials() {
  if (!essentials.length) { specials = null; return render(); }
  if (!code || specialsLoading) return;
  specialsLoading = true; renderSpecials();
  try { specials = await api("GET", `/api/users/${code}/specials`); }
  catch (e) { specials = { error: e.message, items: [] }; }
  specialsLoading = false; render();
}

// 有几件必需品在打折；每件取两家里省得最多的那个算总共能省多少
function specialStats() {
  if (!specials?.items) return { n: 0, save: 0 };
  let n = 0, save = 0;
  for (const r of specials.items) {
    const hot = STORES.filter(s => r[s]?.special);
    if (!hot.length) continue;
    n++;
    save += Math.max(0, ...hot.map(s => { const p = r[s].product; return p.was ? (p.was - p.price) * r.qty : 0; }));
  }
  return { n, save };
}

function renderSpecials() {
  const { n, save } = specialStats();
  $("#specialCount").textContent = n || "";
  $("#specialBanner").hidden = !n;
  $("#specialBannerText").textContent = t("bannerSpecials", { n });
  $("#spTitle").textContent = t("spTitle", { d: config.week || "" });
  renderRemind();
  if (tab !== "specials") return;

  const sum = $("#spSummary"), list = $("#spList");
  if (!essentials.length) { sum.innerHTML = `<div class="msg">${t("spEmpty")}</div>`; list.innerHTML = ""; return; }
  if (specialsLoading || !specials) { sum.innerHTML = `<div class="msg">${t("spChecking", { n: essentials.length })}</div>`; list.innerHTML = ""; return; }
  if (specials.error) { sum.innerHTML = `<div class="msg err">${t("failed")}${esc(specials.error)}</div>`; list.innerHTML = ""; return; }
  sum.innerHTML = `<div class="verdict" style="margin:0">${n ? t("spHits", { n, p: money(save) }) : t("spNoHits")}</div>`;

  // 有特价的排前面
  const rows = [...specials.items].sort((a, b) =>
    STORES.some(s => b[s]?.special) - STORES.some(s => a[s]?.special));
  list.innerHTML = rows.map(r => {
    const hot = STORES.some(s => r[s]?.special);
    return `<div class="sp-item ${hot ? "hot" : ""}">
      <div class="sp-name">${esc(r.label)}${r.qty > 1 ? ` <span class="unit">× ${r.qty}</span>` : ""}<span class="spacer"></span>
        ${r.cheaper ? `<span class="badge win">${t("spCheaperAt", { s: STORE_NAME[r.cheaper] })}</span>` : ""}</div>
      ${STORES.map(s => spSide(r, s)).join("")}
    </div>`;
  }).join("");
}

function spSide(r, store) {
  const x = r[store] || {}, p = x.product;
  const tag = `<div class="store-tag ${store === "coles" ? "c" : "w"}">${STORE_NAME[store]}</div>`;
  if (!p) {
    const why = x.error ? t("failed") + esc(x.error) : x.missing ? t("spMissing") : t("notPicked");
    return `<div class="sp-side">${tag}<div class="msg">${why}</div></div>`;
  }
  const saving = p.was ? `<span class="badge">${t("save", { p: money(p.was - p.price) })}</span>` : "";
  return `<div class="sp-side ${x.special ? "deal" : ""}">${tag}
    <div class="pname"><a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.name)}</a></div>
    <span class="price">${money(p.price)}</span>${p.was ? `<span class="was">${money(p.was)}</span>` : ""}
    <div class="unit">${esc(p.unitLabel || "")}</div>
    <div class="badges">${saving}${badgesFor(p)}</div>
  </div>`;
}

function renderRemind() {
  const body = $("#remindBody");
  if (!config.emailEnabled) { body.innerHTML = `<div class="note">${t("emailOff")}</div>`; return; }
  if (body.dataset.built === prefs.lang) return;  // 避免重绘时清掉正在输入的内容
  body.dataset.built = prefs.lang;
  body.innerHTML = `
    <form class="row" id="remindForm">
      <input type="email" id="emailInput" placeholder="${t("emailPh")}" value="${esc(user.email)}">
      <label class="switch"><input type="checkbox" id="notifyInput" ${user.notify ? "checked" : ""}> ${t("notifyOn")}</label>
      <button class="primary" type="submit">${t("saveBtn")}</button>
      <button type="button" id="testEmailBtn">${t("testBtn")}</button>
    </form>
    <div class="note" id="remindNote"></div>`;
  $("#remindForm").addEventListener("submit", async e => {
    e.preventDefault();
    const note = $("#remindNote");
    const email = $("#emailInput").value.trim(), notify = $("#notifyInput").checked;
    try {
      await api("PUT", `/api/users/${code}/settings`, { email, notify });
      user = { email, notify };
      note.className = "note ok"; note.textContent = t("saved");
    } catch (err) {
      note.className = "note err"; note.textContent = err.message === "invalid email" ? t("invalidEmail") : err.message;
    }
  });
  $("#testEmailBtn").addEventListener("click", async () => {
    const note = $("#remindNote");
    note.className = "note"; note.textContent = "…";
    try {
      const r = await api("POST", `/api/users/${code}/test-email`);
      note.className = "note ok"; note.textContent = r.sent ? t("sentOk") : t("sentNone");
    } catch (err) { note.className = "note err"; note.textContent = err.message; }
  });
}

// ================= 选品弹窗 =================
let pk = null;
function openPicker(item, store) {
  pk = { item, store };
  $("#pkTitle").textContent = `${STORE_NAME[store]} · ${item.label}`;
  $("#pkSearch").value = item.override?.[store] || item.term;
  renderPicker();
  $("#picker").showModal();
}
function renderPicker() {
  const { item, store } = pk;
  const r = results[item.id]?.[store];
  const cur = chosen(item, store);
  if (!r || r.loading) { $("#pkList").innerHTML = `<div class="pk-row">${t("loading")}</div>`; return; }
  if (r.error || !r.items?.length) { $("#pkList").innerHTML = `<div class="pk-row">${esc(r.error || t("pkNone"))}</div>`; return; }
  const rows = [...r.items].sort((a, b) => (a.unitStd === b.unitStd ? (a.unitPrice ?? 1e9) - (b.unitPrice ?? 1e9) : 0));
  $("#pkList").innerHTML = rows.map(p => `
    <div class="pk-row ${cur && cur.id === p.id ? "sel" : ""}" data-pid="${esc(p.id)}">
      ${p.image ? `<img src="${esc(p.image)}" alt="" loading="lazy">` : ""}
      <div class="info">${esc(p.name)}<div class="badges">${badgesFor(p)}</div></div>
      <div class="p"><b>${money(p.price)}</b><div class="unit">${esc(p.unitLabel || "")}</div></div>
    </div>`).join("");
}
$("#pkList").addEventListener("click", e => {
  const row = e.target.closest(".pk-row[data-pid]"); if (!row) return;
  const p = results[pk.item.id][pk.store].items.find(x => String(x.id) === row.dataset.pid);
  pk.item.sel = { ...(pk.item.sel || {}), [pk.store]: p.id };
  syncEssential(pk.item); saveList(); renderList(); $("#picker").close();
});
$("#pkSearch").addEventListener("keydown", async e => {
  if (e.key !== "Enter") return;
  const q = e.target.value.trim(); if (!q) return;
  const { item, store } = pk;
  item.override = { ...(item.override || {}), [store]: q };
  if (item.sel) delete item.sel[store];
  saveList();
  await fetchStore(item, store, true);
  renderPicker();
});
$("#pkClose").onclick = () => $("#picker").close();

// ================= 清单码弹窗 =================
$("#codeBtn").onclick = () => {
  $("#codeBig").textContent = code || "";
  $("#codeInput").value = ""; $("#codeInput").placeholder = code || "";
  $("#codeNote").textContent = "";
  $("#codeDlg").showModal();
};
$("#codeClose").onclick = () => $("#codeDlg").close();
$("#codeForm").addEventListener("submit", async e => {
  e.preventDefault();
  const c = $("#codeInput").value.trim().toUpperCase();
  if (!c || c === code) return $("#codeDlg").close();
  try {
    await loadUser(c);
    $("#codeDlg").close();
    applyI18n(); render(); items.forEach(it => fetchItem(it)); loadSpecials();
  } catch {
    $("#codeNote").className = "note err"; $("#codeNote").textContent = t("codeBad");
  }
});

// ================= 事件 =================
function addItem(raw) {
  const txt = raw.trim(); if (!txt) return;
  const qm = txt.match(/^(.+?)\s*[x×*]\s*(\d{1,2})$/i);   // "香蕉 x3" 表示买 3 件
  const label = qm ? qm[1].trim() : txt;
  const qty = qm ? Math.max(1, +qm[2]) : 1;
  const item = { id: uid(), label, term: toTerm(label), qty };
  items.unshift(item); saveList(); renderList(); fetchItem(item);
}
$("#addForm").addEventListener("submit", e => { e.preventDefault(); addItem($("#addInput").value); $("#addInput").value = ""; });
$("#chips").addEventListener("click", e => { if (e.target.matches(".chip")) addItem(e.target.textContent); });
$("#modeSeg").addEventListener("click", e => {
  const m = e.target.dataset.mode; if (!m) return;
  prefs.mode = m; lsSet(LS.mode, m);
  items.forEach(it => { if (!essentialOf(it)) delete it.sel; });  // 必需品保留已选商品
  saveList(); renderList();
});
$("#langSeg").addEventListener("click", e => {
  const l = e.target.dataset.lang; if (!l) return;
  prefs.lang = l; lsSet(LS.lang, l);
  if (code) api("PUT", `/api/users/${code}/settings`, { lang: l }).catch(() => {});
  applyI18n(); render();
});
document.querySelector(".tabs").addEventListener("click", e => {
  const b = e.target.closest("[data-tab]"); if (!b) return;
  tab = b.dataset.tab; render();
  if (tab === "specials" && !specials) loadSpecials();
});
$("#specialBanner").addEventListener("click", e => {
  if (e.target.dataset.goto) { tab = "specials"; render(); }
});
$("#newWeekBtn").onclick = startNewWeek;
$("#refreshBtn").onclick = () => items.forEach(it => fetchItem(it, true));
$("#clearBtn").onclick = () => { if (confirm(t("confirmClear"))) { items = []; saveList(); renderList(); } };
$("#list").addEventListener("click", e => {
  const btn = e.target.closest("[data-act]"); if (!btn) return;
  const it = items.find(x => x.id === btn.closest(".item").dataset.id);
  const act = btn.dataset.act;
  if (act === "star") return toggleEssential(it);
  if (act === "pick") return openPicker(it, btn.dataset.store);
  if (act === "retry") return fetchStore(it, btn.dataset.store, true);
  if (act === "inc") it.qty++;
  if (act === "dec") it.qty = Math.max(1, it.qty - 1);
  if (act === "del") items = items.filter(x => x !== it);
  if (act === "term") {
    const q = prompt(t("promptTerm"), it.term);
    if (!q || !q.trim()) return;
    it.term = q.trim(); it.sel = {}; it.override = {}; delete results[it.id];
    saveList(); renderList(); fetchItem(it, true);
    return;
  }
  if (act === "inc" || act === "dec") syncEssential(it);
  saveList(); renderList();
});

// ================= 启动 =================
(async function start() {
  applyI18n(); render();
  try {
    config = await api("GET", "/api/config");
    await initUser();
  } catch (e) {
    $("#list").innerHTML = `<div class="empty">${t("noServer")}<br>${esc(e.message)}</div>`;
    return;
  }
  applyI18n(); render();
  items.forEach(it => fetchItem(it));
  loadSpecials();  // 后台检查本周特价，有的话显示提醒横幅
})();
