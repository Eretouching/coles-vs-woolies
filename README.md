# Coles vs Woolworths Price Check

**English** · [中文](README.zh-CN.md)

Type your shopping list (in English or Chinese) and compare live prices at Coles and Woolworths in Australia.
Self-hosted, no accounts, one small Python server with a SQLite file.

> ## ⚠️ Must run from an Australian IP address
> Coles and Woolworths do not serve this tool from IP addresses **outside Australia**. Deployed on a
> Singapore server, every price lookup fails with HTTP 502. Run it on your own computer or home network
> in Australia, or host it on a server **located in Australia** (see [Deploy](#deploy)). Choosing an
> overseas region on a cloud platform will not work, no matter how close it is.

## Features

- **Compare**: which store is cheaper for the whole list and for each item (by unit price, multi-buy
  deals like "2 for $X" included), and how much you save by splitting the shop.
- **Auto-pick**: "Most relevant" or "Cheapest per unit" globally, or per item. Cheapest only compares
  products in the same category (fresh blueberries are never swapped for frozen ones or muffins).
- **Pick memory**: products you choose with "Change" are remembered and reused next time.
- **Coles store selection**: choose your Coles store by postcode or suburb. Woolworths store-specific
  pricing needs a login, so Woolworths always uses its online default prices.
- **Weekly essentials**: star the things you buy every week and reload them in one click.
- **Weekly specials alerts**: both stores change prices on Wednesdays. See which of your essentials are on
  special, and optionally get an email every Wednesday morning.
- **One-click add to trolley**: a bookmarklet adds the list to your trolley on the supermarket's own site,
  using your own logged-in session. Your password never touches this server, and nothing is checked out or paid.
  Nothing is doubled or dropped: each item goes to exactly one store, quantities are set exactly, and the
  trolley is verified afterwards.
- **Prices refreshed weekly**: prices are cached for a whole week and a background job refreshes them slowly
  every Wednesday 7:00 (Sydney time). There is no "refresh everything" button, to avoid being blocked.
- **Refresh a single item**: the ↻ next to an item fetches its latest price at both stores right now. To stay
  polite, the same search term is fetched at most once every 10 minutes (extra clicks reuse the fresh data) and each
  IP gets 30 refreshes per hour. If the fetch fails, the previous price is kept.
- **Bilingual UI** (中文 / English) and **multi-device sync** through an 8-character list code (no sign-up).

## Requirements

- **An Australian IP address** (see the warning above).
- Python 3.9+ and `curl` (Coles blocks Python's HTTP client but allows `curl`). No pip packages.
- Or just Docker.

## Run locally

```bash
python3 server.py
```

Open http://localhost:8765. On macOS you can also double-click `启动比价.command`.

Everything is stored in `./data/app.db`, including the price cache, so restarting the program does not
re-fetch prices. Within the same price week (Wednesday 07:00 to the next Wednesday) it only reads the saved
prices. When you open it in a new week, only the items you have selected (your current list and weekly
essentials) get fresh prices; other searches are fetched only if you look them up.

## Deploy

The server needs three things: **an Australian IP**, **a persistent volume mounted at `/data`**
(otherwise every redeploy wipes users' lists and the price cache), and an always-on process
(the Wednesday job runs inside the server; a service that sleeps when idle will run it late).

### Docker on an Australian server (recommended)

Any VPS or cloud instance located in Australia works (Sydney, Melbourne...).

```bash
git clone https://github.com/Eretouching/coles-vs-woolies.git
cd coles-vs-woolies
docker build -t coles-vs-woolies .
docker run -d --name price-check --restart unless-stopped \
  -p 8080:8080 -v price-check-data:/data \
  --env-file .env \
  coles-vs-woolies
```

Copy [`.env.example`](.env.example) to `.env` for the optional settings (email, etc.). Put a reverse proxy
with HTTPS (Caddy, nginx...) in front. Health check: `GET /healthz`.

### Zeabur / other container platforms

Only if the platform can run your service in an Australian region. Check that before you start, and after
deploying open `/api/search?store=woolworths&q=milk` and `/api/search?store=coles&q=milk`: if you see product
JSON it works; if you get an `error`, the platform's IP is being blocked.

1. Create a service from your fork of this repository. The `Dockerfile` is detected automatically.
2. Add a **volume**: Volume ID `data`, mount directory `/data` (Zeabur: service → Volumes). Mounted volumes
   disable zero-downtime restarts, so each restart has a short outage; data is kept. Without the volume the
   startup log prints a warning.
3. Expose port `8080` and generate a domain.
4. Optionally add the environment variables below.

## Configuration

All environment variables are optional. See [`.env.example`](.env.example).

| Variable | Default | Description |
|---|---|---|
| `HOST` | `127.0.0.1` (Docker image: `0.0.0.0`) | Address to listen on |
| `PORT` | `8765` (Docker image: `8080`) | Port to listen on |
| `DATA_DIR` | `./data` (Docker image: `/data`) | Where `app.db` is stored. Must be persistent in production |
| `WEEKLY_REFRESH` | `selected` (Docker image: `all`) | What the Wednesday job refreshes. `selected`: only each user's current list and weekly essentials. `all`: also every term searched in the last three weeks, so everyone gets instant results (for shared servers) |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` | – | Outgoing mail for weekly specials emails. Without `SMTP_HOST` and `SMTP_USER`, specials only show in the web page. Port 587 = STARTTLS, 465 = SSL. Gmail needs an app password |
| `APP_URL` | – | Link used inside the emails |
| `COLES_BFF_KEY` | read automatically | Public front-end key used by Coles store search. Only set it if Coles' web page is blocked: open coles.com.au, run `__RUNTIME_CONFIG__.BFF_API_SUBSCRIPTION_KEY` in the browser console |

## Operations

- **Weekly job**: every Wednesday from 07:00 Sydney time (or when the program is first started in a new week)
  the server slowly refreshes prices (5 s between Coles requests, 2 s between Woolworths requests): weekly
  essentials first, then current lists, then sends specials emails, then (`WEEKLY_REFRESH=all` only) other searched terms. If Coles
  blocks it, it pauses 15 minutes and retries; unfinished work is retried an hour later.
- **Backup**: everything lives in `$DATA_DIR/app.db` (SQLite, WAL mode). Back it up with
  `sqlite3 app.db ".backup backup.db"`, or stop the server and copy `app.db`, `app.db-wal`, `app.db-shm`.
- **Upgrade**: pull, rebuild, restart. New database columns are added automatically.
- **Logs**: the server prints API requests and the weekly job's progress to stdout.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Every price lookup returns 502 | Not running from an Australian IP. Move the server to Australia |
| Only Coles fails: "blocked by Coles anti-bot" | Temporary. Coles rate-limits; the server pauses Coles requests for 10 minutes. Try again later |
| Coles store search fails | Set `COLES_BFF_KEY` (see above) |
| Lists disappear after redeploying | `/data` is not a persistent volume |
| No specials emails | `SMTP_HOST`/`SMTP_USER` not set, the user hasn't enabled alerts, or the service was asleep on Wednesday |
| One-click trolley says "please log in" | Log in on the supermarket's site first, then click the bookmark again. After the site changes, the bookmarklet may need updating |

## How it works

| File | Purpose |
|---|---|
| `server.py` | HTTP server, JSON API, per-IP rate limits |
| `stores.py` | Talks to Coles and Woolworths (Woolworths JSON search API; Coles Next.js data endpoint through `curl`) |
| `db.py` | SQLite: users (list code), lists, essentials, pick memory, settings |
| `pricecache.py` | Weekly price cache, valid until the next Wednesday 07:00 Sydney time |
| `weekly.py` | Wednesday job: slow refresh, specials check, emails |
| `static/` | Web UI (`app.js`, `app.css`, `dict.js` Chinese→English search terms) |
| `static/cart-bookmarklet.js` | Source of the "add to trolley" bookmarklet (runs on the supermarket site) |

<details>
<summary>API</summary>

| Method | Path | Description |
|---|---|---|
| GET | `/api/search?store=coles\|woolworths&q=&storeId=&fresh=1` | Search products (`storeId` is a Coles store id, optional; `fresh=1` fetches live, rate-limited) |
| GET | `/api/stores?q=2067` | Find nearby Coles stores by postcode/suburb |
| POST | `/api/users` | Create a list code |
| GET | `/api/users/{code}` | Read list, essentials and settings |
| PUT | `/api/users/{code}/list` · `/essentials` · `/picks` · `/settings` | Save |
| GET | `/api/users/{code}/specials` | Check this week's specials for the essentials |
| POST | `/api/users/{code}/test-email` | Send a specials email now |
| GET | `/healthz` | Health check |

</details>

## Privacy and security

- The server stores, per list code: the shopping list, essentials, remembered product picks, your Coles store, language,
  and (only if you enter it) your email address. No passwords and no supermarket accounts are ever handled.
- **Whoever knows a list code can read and edit that list.** Treat it like a password and don't post it publicly.
- Rate limits are per client IP. Behind a reverse proxy, make sure it sets `X-Forwarded-For` and the app port is
  not reachable directly from the internet.

## Disclaimer

This is an independent, unofficial project. It is **not affiliated with, endorsed by, or connected to Coles
Group or Woolworths Group**. It reads the same public product pages you would see in a browser. Their terms of
use may restrict automated access, so use it responsibly: personal or small-scale use only, don't run high-volume
scrapers, and respect the built-in weekly caching. Prices may differ in store, and the tool may stop working at
any time if the supermarkets change their websites. Provided as is, without warranty.

## Contributing

Issues and pull requests are welcome, especially when a supermarket changes its site. The code deliberately has
no third-party dependencies, please keep it that way. Useful checks before a PR: `python3 -m py_compile *.py`
and `node --check static/app.js static/cart-bookmarklet.js`.

## License

[MIT](LICENSE)
