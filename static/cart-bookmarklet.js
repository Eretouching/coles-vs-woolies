// 「一键加购」书签脚本：在 coles.com.au / woolworths.com.au 上运行，
// 用你当前登录的账号，把比价工具生成的购物单加入超市购物车。
// 密码不经过比价工具的服务器；只加入购物车，不会结账或付款。
//
// 购物单从网址的 #cvw=... 读取（比价工具打开超市网站时会带上），
// 读不到就尝试剪贴板，再不行就让你粘贴「加购码」。
// 这个文件由 app.js 读取后编码成 javascript: 书签（保留换行，所以可以写 // 注释）。
(async () => {
  const host = location.hostname;
  const store = /coles\.com\.au$/.test(host) ? "coles" : /woolworths\.com\.au$/.test(host) ? "woolworths" : null;
  const zh = (navigator.language || "").startsWith("zh");
  const T = (a, b) => (zh ? a : b);
  if (!store) return alert(T("请在 coles.com.au 或 woolworths.com.au 页面上点这个书签。", "Use this bookmark on coles.com.au or woolworths.com.au."));

  const decode = raw => {
    const m = String(raw || "").match(/cvw=([A-Za-z0-9_\-]+)/);
    if (!m) return null;
    try {
      const b64 = m[1].replace(/-/g, "+").replace(/_/g, "/");
      const bin = atob(b64);
      return JSON.parse(new TextDecoder().decode(Uint8Array.from(bin, c => c.charCodeAt(0))));
    } catch { return null; }
  };
  let order = decode(location.hash);
  if (!order) { try { order = decode(await navigator.clipboard.readText()); } catch {} }
  if (!order) order = decode(prompt(T("粘贴比价工具里的「加购码」：", "Paste the cart code from the price checker:")));
  if (!order) return;
  if (order.s !== store) {
    return alert(T(`这份购物单是给 ${order.s === "coles" ? "Coles" : "Woolworths"} 的，请到对应网站上再点书签。`,
      `This list is for ${order.s === "coles" ? "Coles" : "Woolworths"}. Open that site and try again.`));
  }

  // ---------- 进度浮层 ----------
  const box = document.createElement("div");
  box.style.cssText = "position:fixed;z-index:2147483647;top:16px;right:16px;width:340px;max-height:70vh;overflow:auto;" +
    "background:#fff;color:#1d1d1b;border-radius:14px;box-shadow:0 12px 40px rgba(0,0,0,.3);padding:16px;" +
    "font:14px/1.5 -apple-system,'PingFang SC',sans-serif";
  document.body.appendChild(box);
  const show = html => { box.innerHTML = html + `<div style="text-align:right;margin-top:10px"><button id="cvw-x" style="border:1px solid #ddd;background:#fff;border-radius:8px;padding:4px 12px;cursor:pointer">${T("关闭", "Close")}</button></div>`; box.querySelector("#cvw-x").onclick = () => box.remove(); };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  show(`<b>🛒 ${T("正在加入购物车…", "Adding to trolley…")}</b><br>${order.i.length} ${T("件商品", "items")}`);

  // 同一件商品出现多次就合并数量（比价工具已经合并过，这里再保险一次）
  const wantMap = new Map();
  for (const [id, qty, name] of order.i) {
    const k = String(id), e = wantMap.get(k) || { id: k, qty: 0, name };
    e.qty += Math.max(1, qty | 0); wantMap.set(k, e);
  }
  const items = [...wantMap.values()];
  // 分给另一家的商品：如果已经在这家购物车里，要移除，避免两边重复买
  const excludes = (order.x || []).map(([id, name]) => ({ id: String(id), name })).filter(x => !wantMap.has(x.id));

  let getTrolley, setQty;  // getTrolley() → Map(商品编号 → 数量)；setQty([{id, qty}]) 把数量设成准确值（0 = 移除）
  try {
    if (store === "woolworths") {
      const api = (path, body) => fetch("/apis/ui/Trolley" + path, {
        method: body ? "POST" : "GET", credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      }).then(r => { if (!r.ok) throw new Error(`Woolworths HTTP ${r.status}`); return r.json(); });
      getTrolley = async () => new Map(Object.values(await api("")).filter(Array.isArray).flat()
        .filter(x => x && x.Stockcode != null).map(x => [String(x.Stockcode), x.QuantityInTrolley || 0]));
      setQty = async list => { for (const it of list) await api("/UpdateItem", { stockcode: Number(it.id), quantity: it.qty }).catch(() => null); };
    } else {
      const key = (window.__RUNTIME_CONFIG__ || {}).BFF_API_SUBSCRIPTION_KEY;
      const cookie = name => decodeURIComponent((document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)")) || [])[1] || "");
      // 门店号：和 Coles 网站一样，先用它保存的购物方式，再用 cookie
      let sid = "";
      try { sid = JSON.parse(localStorage.getItem("shoppingMethod") || "{}").currentFulfilmentStoreId || ""; } catch {}
      sid = String(sid || cookie("fulfillmentStoreId") || "");
      if (!key) throw new Error(T("读不到 Coles 网站配置，请刷新页面后再试", "Coles page not ready, reload and try again"));
      if (!sid) throw new Error(T("请先在 Coles 网站上选择门店（右上角 Set your location）", "Choose a store on Coles first (Set your location)"));
      // Coles 网站自己发请求时带的请求头：key、会话/访客/用户 ID（来自它的 cookie）、追踪 ID
      const headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": key,
        "cusp-session-id": cookie("sessionId"),
        "cusp-visitor-id": cookie("visitorId"),
        "cusp-user-id": cookie("dsch-ccpuserid"),
      };
      const api = async (method, body, step) => {
        const r = await fetch(`/api/bff/trolley/store/${sid}`, {
          method, credentials: "include",
          headers: { ...headers, "cusp-correlation-id": crypto.randomUUID() },
          body: body ? JSON.stringify(body) : undefined,
        });
        if (r.status === 401 || r.status === 403) throw new Error(T("请先登录 Coles 账号", "Please log in to Coles first"));
        if (!r.ok) {
          const text = (await r.text().catch(() => "")).slice(0, 200);
          throw new Error(`${step} · HTTP ${r.status} · store ${sid}<br><code style="font-size:11px;word-break:break-all">${esc(text)}</code>`);
        }
        return r.json();
      };
      getTrolley = async () => new Map(((await api("GET", null, "GET trolley")).allItems || [])
        .map(x => [String(x.productId), x.quantity || 0]));
      setQty = list => api("PATCH", {
        ageGateVerified: false, swapBehaviour: false,
        items: [{ actions: list.map(it => ({ productId: it.id, quantity: it.qty })) }],
      }, "PATCH trolley");
    }

    const before = await getTrolley().catch(e => (/登录|log in/i.test(e.message) ? Promise.reject(e) : new Map()));
    // 数量设成准确值：重复点书签不会翻倍，之前多加的也会改回来
    const removeNow = excludes.filter(x => (before.get(x.id) || 0) > 0);
    await setQty([...items.map(it => ({ id: it.id, qty: it.qty })), ...removeNow.map(x => ({ id: x.id, qty: 0 }))]);

    // 逐件核对：购物车里的数量必须和购物单一致
    const after = await getTrolley();
    const ok = [], wrong = [], missing = [], stillThere = [];
    for (const it of items) {
      const got = after.get(it.id) || 0;
      (got === it.qty ? ok : got === 0 ? missing : wrong).push({ ...it, got });
    }
    for (const x of removeNow) if ((after.get(x.id) || 0) > 0) stillThere.push(x);
    const removed = removeNow.filter(x => !stillThere.includes(x));
    const units = ok.reduce((a, x) => a + x.qty, 0);
    const li = list => `<ul style="margin:6px 0;padding-left:18px">${list.join("")}</ul>`;
    const allGood = !wrong.length && !missing.length && !stillThere.length;

    history.replaceState(null, "", location.pathname + location.search);  // 清掉网址里的购物单
    show(`<b>${allGood ? "✅" : "⚠️"} ${T(`已核对：${ok.length}/${items.length} 种商品数量正确（共 ${units} 件）`,
        `Checked: ${ok.length}/${items.length} products with the right quantity (${units} units)`)}</b>` +
      (missing.length ? `<br><br><b style="color:#e01a22">${T("没加进去（可能缺货或本店没有），请在另一家买：", "Not added (out of stock or not sold here), buy at the other store:")}</b>` +
        li(missing.map(m => `<li>${esc(m.name || m.id)} × ${m.qty}</li>`)) : "") +
      (wrong.length ? `<br><b style="color:#e01a22">${T("数量不对（可能有限购）：", "Wrong quantity (maybe a purchase limit):")}</b>` +
        li(wrong.map(w => `<li>${esc(w.name || w.id)}：${T("需要", "want")} ${w.qty}，${T("购物车里", "in trolley")} ${w.got}</li>`)) : "") +
      (removed.length ? `<br>${T("已从购物车移除（这些分给了另一家）：", "Removed from trolley (assigned to the other store):")}` +
        li(removed.map(x => `<li>${esc(x.name || x.id)}</li>`)) : "") +
      (stillThere.length ? `<br><b style="color:#e01a22">${T("这些分给了另一家，但没能从购物车移除，请手动删除：", "Assigned to the other store but couldn't be removed, delete them yourself:")}</b>` +
        li(stillThere.map(x => `<li>${esc(x.name || x.id)}</li>`)) : "") +
      (store === "woolworths"
        ? `<br><a href="/shop/cart" style="color:#178841;font-weight:600">${T("打开购物车 →", "Open trolley →")}</a>`
        : `<br><a href="javascript:location.reload()" style="color:#e01a22;font-weight:600">${T("刷新页面，然后点右上角购物车查看 →", "Reload, then open the trolley (top right) →")}</a>`));
  } catch (e) {
    // 错误信息是本脚本自己拼的（Coles 返回的内容已经转义过）
    return show(`<b>⚠️ ${T("加购失败", "Couldn't add items")}</b><br>${e instanceof TypeError ? esc(e.message) : e.message}`);
  }
})();
