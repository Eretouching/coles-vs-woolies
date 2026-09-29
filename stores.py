"""Coles 和 Woolworths 的商品搜索（只用 Python 标准库 + 系统 curl）。"""
import gzip
import http.cookiejar
import json
import os
import re
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 30 * 60  # 秒（门店列表等小数据的内存缓存；商品价格按周缓存，见 pricecache.py）
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")

_cache = {}
_cache_lock = threading.Lock()


def cached(key, fn):
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL:
            return hit[1]
    value = fn()
    with _cache_lock:
        _cache[key] = (now, value)
    return value


def _read(resp):
    data = resp.read()
    if resp.headers.get("Content-Encoding") == "gzip":
        data = gzip.decompress(data)
    return data.decode("utf-8", "replace")


# ---------- 单价归一化：统一成 每kg / 每L / 每个（张） ----------

UNIT_SCALE = {"g": ("kg", 1000), "kg": ("kg", 1), "ml": ("L", 1000), "l": ("L", 1),
              "ea": ("each", 1), "each": ("each", 1),
              "sheet": ("each", 1), "sheets": ("each", 1)}


def parse_unit_label(label):
    """把网站显示的单价 "$1.65/ 1L"、"$0.20 / 100 sheets" 换算成 (每标准单位价格, 标准单位)。

    直接用网站显示的文字，因为 Coles 原始字段对散装商品（如香蕉）有时单位是错的。
    """
    m = re.match(r"\s*\$([\d.,]+)\s*/\s*([\d.]*)\s*([A-Za-z]+)", label or "")
    if not m:
        return None, None
    price, qty, unit = float(m.group(1).replace(",", "")), float(m.group(2) or 1), m.group(3).lower()
    if unit not in UNIT_SCALE or not qty:
        return None, None
    std, factor = UNIT_SCALE[unit]
    return round(price / qty * factor, 4), std


def parse_multibuy(text):
    """从 "2 for $5.80" / "Pick any 2 for $24" 这类文字里提取多买优惠。"""
    m = re.search(r"(\d+)\s+for\s+\$([\d.]+)", text, re.I)
    if not m:
        return None
    qty, total = int(m.group(1)), float(m.group(2))
    if qty < 2:
        return None
    price = f"{total:.2f}".removesuffix(".00")
    return {"text": f"{qty} for ${price}", "minQty": qty, "each": round(total / qty, 2)}


def demote_sponsored(items):
    """付费推广的商品排到最后，避免"最相关"被广告占据。"""
    return [p for p in items if not p["sponsored"]] + [p for p in items if p["sponsored"]]


# ---------- Woolworths ----------

class Woolworths:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.opener.addheaders = [("User-Agent", UA), ("Accept-Language", "en-AU,en;q=0.9")]
        self.lock = threading.Lock()
        self.primed = False

    def _prime(self):
        with self.lock:
            if not self.primed:
                self.opener.open("https://www.woolworths.com.au/", timeout=20).read()
                self.primed = True

    def search(self, term, store_id=None, size=12):
        # Woolworths 按门店查价需要登录账号，这里只能用网上默认价，store_id 不起作用
        self._prime()
        body = json.dumps({
            "SearchTerm": term, "PageSize": size, "PageNumber": 1,
            "SortType": "TraderRelevance",
            "Location": "/shop/search/products?searchTerm=" + urllib.parse.quote(term),
        }).encode()
        req = urllib.request.Request(
            "https://www.woolworths.com.au/apis/ui/Search/products", data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"})
        try:
            data = json.loads(_read(self.opener.open(req, timeout=20)))
        except urllib.error.HTTPError:
            self.primed = False  # cookie 过期，下次重新获取
            raise
        out = []
        for group in data.get("Products") or []:
            for p in group.get("Products") or []:
                out.append(self._convert(p))
        return demote_sponsored(out)

    def locate(self, query):
        """把邮编或区名换算成经纬度：借用 Woolworths 门店定位接口，取最近一家店的坐标。"""
        self._prime()
        url = ("https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=1&Division=SUPERMARKETS"
               "&Facility=&postcode=" + urllib.parse.quote(query))
        stores = json.loads(_read(self.opener.open(url, timeout=20))).get("Stores") or []
        if not stores:
            return None
        return float(stores[0]["Latitude"]), float(stores[0]["Longitude"])

    @staticmethod
    def _convert(p):
        unit_price, std = parse_unit_label(p.get("CupString")) if p.get("HasCupPrice") else (None, None)
        price, was = p.get("Price"), p.get("WasPrice")
        promo = None
        if p.get("IsHalfPrice"):
            promo = "half"
        elif p.get("IsOnSpecial"):
            promo = "special"
        multibuy = parse_multibuy((p.get("CentreTag") or {}).get("TagContent") or "")
        return {
            "store": "woolworths",
            "id": p.get("Stockcode"),
            "name": p.get("DisplayName") or p.get("Name"),
            "size": p.get("PackageSize"),
            "price": price,
            "was": was if was and price and was > price else None,
            "promo": promo,
            "multibuy": multibuy,
            "unitPrice": unit_price,
            "unitStd": std,
            "unitLabel": p.get("CupString"),
            "available": bool(p.get("IsAvailable", True)) and p.get("IsInStock", True),
            # 细分类（如 BLUEBERRY / FREEZER - FRUIT），「单价最便宜」只在同类商品里比较
            "category": (p.get("AdditionalAttributes") or {}).get("sapsubcategoryname"),
            "sponsored": "Promoted" in (p.get("Source") or ""),
            "image": p.get("MediumImageFile"),
            "url": f"https://www.woolworths.com.au/shop/productdetails/{p.get('Stockcode')}/{p.get('UrlFriendlyName', '')}",
        }


# ---------- Coles ----------

class StaleBuild(Exception):
    pass


class Coles:
    IMG = "https://cdn.productimages.coles.com.au/productimages"

    # Coles 的防爬虫（Imperva）会拦截 Python 自带的 HTTP 客户端，但放行系统自带的 curl。
    # 网页 HTML 容易被拦，而数据接口 /_next/data/<buildId>/... 基本不拦，
    # 所以只在 buildId 过期（网站更新）时才去抓一次网页，并把 buildId 存到本地文件。
    # 选门店：Coles 网站用 cookie "fulfillmentStoreId" 决定显示哪家门店的价格，不需要登录。
    # 门店列表接口需要网页里公开的前端 key（BFF_API_SUBSCRIPTION_KEY），和 buildId 一起从网页里读出来。
    BUILD_ID_FILE = DATA_DIR / "coles_build_id.txt"
    KEY_FILE = DATA_DIR / "coles_bff_key.txt"

    def __init__(self):
        self.build_id = self.BUILD_ID_FILE.read_text().strip() if self.BUILD_ID_FILE.exists() else None
        self.bff_key = os.environ.get("COLES_BFF_KEY") or (
            self.KEY_FILE.read_text().strip() if self.KEY_FILE.exists() else None)
        self.lock = threading.Lock()
        self.req_lock = threading.Lock()
        self.last_req = 0.0
        self.page_failed_at = 0.0
        self.blocked_until = 0.0  # 断路器：被拦截后暂停所有 Coles 请求一段时间

    BLOCK_COOLDOWN = 10 * 60

    def _curl(self, url, extra=()):
        # 被拦截期间不再发请求：继续请求只会让拦截时间更长
        if time.time() < self.blocked_until:
            raise RuntimeError("blocked by Coles anti-bot, paused for a few minutes")
        # 一次只发一个请求，且间隔一点时间，避免触发防爬虫
        with self.req_lock:
            wait = self.last_req + 0.3 - time.time()
            if wait > 0:
                time.sleep(wait)
            try:
                r = subprocess.run(
                    ["curl", "-s", "--compressed", "-m", "20", "-A", UA,
                     "-H", "Accept-Language: en-AU,en;q=0.9", *extra, "-w", "\n%{http_code}", url],
                    capture_output=True, text=True)
            finally:
                self.last_req = time.time()
        body, _, code = r.stdout.rpartition("\n")
        if code == "404" and "/_next/data/" in url:
            raise StaleBuild()
        if r.returncode or code != "200":
            raise RuntimeError(f"Coles HTTP {code or r.returncode}")
        if "Pardon Our Interruption" in body[:2000]:
            self.blocked_until = time.time() + self.BLOCK_COOLDOWN
            raise RuntimeError("blocked by Coles anti-bot, try again in a few minutes")
        return body

    def _refresh_build_id(self, stale):
        with self.lock:
            if self.build_id and self.build_id != stale:
                return self.build_id  # 其他线程已经更新过了
            if time.time() - self.page_failed_at < 600:
                raise RuntimeError("Coles page temporarily blocked, try again in a few minutes")
            try:
                html = self._curl("https://www.coles.com.au/search/products?q=milk")
            except RuntimeError:
                self.page_failed_at = time.time()  # 网页被拦时 10 分钟内不再重试，免得越试越被拦
                raise
            m = re.search(r'"buildId":"([^"]+)"', html)
            if not m:
                raise RuntimeError("cannot find Coles buildId (site layout may have changed)")
            self.build_id = m.group(1)
            self.BUILD_ID_FILE.write_text(self.build_id)
            k = re.search(r'"BFF_API_SUBSCRIPTION_KEY":"([^"]+)"', html)
            if k and not os.environ.get("COLES_BFF_KEY"):
                self.bff_key = k.group(1)
                self.KEY_FILE.write_text(self.bff_key)
            return self.build_id

    def search(self, term, store_id=None, size=12):
        q = urllib.parse.quote(term)
        cookie = ("-b", f"fulfillmentStoreId={store_id}") if store_id else ()
        bid = self.build_id or self._refresh_build_id(None)
        try:
            data = json.loads(self._curl(f"https://www.coles.com.au/_next/data/{bid}/en/search/products.json?q={q}", cookie))
        except StaleBuild:
            bid = self._refresh_build_id(bid)
            data = json.loads(self._curl(f"https://www.coles.com.au/_next/data/{bid}/en/search/products.json?q={q}", cookie))
        results = (data.get("pageProps") or {}).get("searchResults") or {}
        out = [self._convert(p) for p in results.get("results") or []
               if p.get("_type") == "PRODUCT" and p.get("pricing")]
        return demote_sponsored(out)[:size]

    def nearby_stores(self, lat, lng):
        """某个坐标附近 50km 内的 Coles 门店（Click & Collect 门店列表，按距离排序）。"""
        if not self.bff_key:
            self._refresh_build_id(self.build_id)  # 顺便从网页里读出 key
        if not self.bff_key:
            raise RuntimeError("Coles store search unavailable")
        url = (f"https://www.coles.com.au/api/bff/locations/search?latitude={lat}&longitude={lng}"
               "&distance=50&numberOfLocations=20")
        data = json.loads(self._curl(url, ("-H", f"Ocp-Apim-Subscription-Key: {self.bff_key}")))
        out, seen = [], set()
        for loc in data.get("locations") or []:
            sid = (loc.get("fulfillmentStore") or {}).get("storeId")
            name = loc.get("locationName") or ""
            # 同一家店会有多个取货点；另外去掉"仅限加盟商"之类的特殊取货点
            if not sid or sid in seen or not name.startswith("Coles"):
                continue
            seen.add(sid)
            out.append({"id": sid, "name": name.replace(" - Drive-through", ""),
                        "address": loc.get("address"), "suburb": loc.get("suburb"),
                        "postcode": loc.get("postcode"), "state": loc.get("state"),
                        "distance": (loc.get("distance") or {}).get("description")})
        return out

    def _convert(self, p):
        pr = p["pricing"]
        unit_price, std = parse_unit_label(pr.get("comparable"))
        promo = None
        if pr.get("promotionType") == "SPECIAL" or pr.get("was"):
            promo = "special"
        multibuy = parse_multibuy(pr.get("offerDescription") or "")
        imgs = p.get("imageUris") or []
        slug = re.sub(r"[^a-z0-9]+", "-", f"{p.get('brand', '')} {p.get('name', '')} {p.get('size', '')}".lower()).strip("-")
        return {
            "store": "coles",
            "id": p.get("id"),
            "name": " ".join(x for x in [p.get("brand"), p.get("name"), p.get("size")] if x),
            "size": p.get("size"),
            "price": pr.get("now"),
            "was": pr.get("was") or None,
            "promo": promo,
            "multibuy": multibuy,
            "unitPrice": unit_price,
            "unitStd": std,
            "unitLabel": pr.get("comparable"),
            "available": bool(p.get("availability", True)),
            # 货架通道（如 Berries & Cherries / Frozen Fruit），「单价最便宜」只在同类商品里比较
            "category": ((p.get("onlineHeirs") or [{}])[0] or {}).get("aisle"),
            "sponsored": bool(p.get("adId") or p.get("featured")),
            "image": self.IMG + imgs[0]["uri"] if imgs else None,
            "url": f"https://www.coles.com.au/product/{slug}-{p.get('id')}",
        }


STORES = {"woolworths": Woolworths(), "coles": Coles()}


_key_locks = {}
_key_locks_lock = threading.Lock()


def search(store, term, store_id=None, with_time=False):
    """搜索商品，供 HTTP 接口和每周特价检查共用。store_id 是门店编号（目前只有 Coles 支持）。

    价格每周三更新，所以结果按周缓存在数据库里（见 pricecache.py）：本周查过就直接用，
    没查过才实时查一次。with_time=True 时同时返回这份数据的抓取时间。
    """
    import pricecache  # 避免循环导入（pricecache 用到本模块的 DATA_DIR）
    if store != "coles":
        store_id = None
    hit = pricecache.get(store, store_id, term)
    if not hit:
        # 同一个词同时被多人搜索时，只向超市发一次请求
        k = (store, store_id, term.strip().lower())
        with _key_locks_lock:
            lock = _key_locks.setdefault(k, threading.Lock())
        with lock:
            hit = pricecache.get(store, store_id, term)
            if not hit:
                items = STORES[store].search(term, store_id)
                hit = items, pricecache.put(store, store_id, term, items)
    return hit if with_time else hit[0]


def refresh(store, term, store_id=None):
    """每周更新任务用：不管缓存，直接重新查一次并存起来。"""
    import pricecache
    items = STORES[store].search(term, store_id if store == "coles" else None)
    pricecache.put(store, store_id if store == "coles" else None, term, items)
    return items


def find_product(store, pid, terms, store_id=None):
    """按商品 ID 找回某个商品的最新价格：依次用各个关键词搜索，直到找到这个 ID。"""
    for term in terms:
        if not term:
            continue
        for p in search(store, term, store_id):
            if str(p["id"]) == str(pid):
                return p
    return None


def nearby_coles_stores(query):
    """按邮编或区名找附近的 Coles 门店。"""
    def fetch():
        loc = STORES["woolworths"].locate(query)
        return STORES["coles"].nearby_stores(*loc) if loc else []
    return cached(("coles-stores", query.lower()), fetch)
