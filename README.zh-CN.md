# Coles vs Woolworths 比价

[English](README.md) · **中文**

输入购物清单（中文或英文），实时比较澳洲 Coles 和 Woolworths 的价格。可自己部署，不用注册账号，
一个小型 Python 服务器加一个 SQLite 文件就够了。

> ## ⚠️ 必须在澳洲 IP 上运行
> Coles 和 Woolworths **不接受来自澳洲境外 IP 的访问**。实测部署在新加坡的服务器上，所有价格查询都返回 HTTP 502。
> 请在你自己澳洲境内的电脑或家庭网络上运行，或者部署在**位于澳洲的服务器**上（见[部署](#部署)）。
> 云平台上选海外区域是行不通的，再近也不行。

## 功能

- **比价**：整单去哪家便宜、每件商品哪家便宜（按单价比，自动算「2 for $X」这类多买优惠）、两家分开买能省多少。
- **自动选品**：全局选「最相关」或「单价最便宜」，每件商品也可以单独切换。「最便宜」只在同一分类里比较
  （新鲜蓝莓不会被换成冷冻蓝莓或蓝莓松饼）。
- **选品记忆**：在「换一个」里挑过的商品会被记住，下次自动选中。
- **Coles 门店选择**：输入邮编或区名，选你常去的 Coles 门店。Woolworths 按门店查价需要登录账号，
  所以 Woolworths 一直用网上默认价。
- **每周必需品**：点 ☆ 标记每周都买的东西，下周一键载入。
- **每周特价提醒**：两家每周三换价格和特价。可以查看必需品哪些在打折，也可以在每周三早上收到邮件。
- **一键加入购物车**：书签在超市官网上、用你自己已登录的账号把清单加进购物车。密码不经过本服务器，
  也不会结账付款。不重复、不丢货：每件商品只分到一家，数量设成准确值，加完后逐件核对购物车。
- **价格每周更新一次**：价格缓存一整周，后台任务每周三 7:00（悉尼时间）慢慢重新查一遍。没有「全部刷新」
  按钮，以免被拦截。
- **单个货品实时刷新**：点商品名旁边的 ↻，立刻去两家抓这一件的最新价格。为了不被拦截：同一个搜索词 10 分钟内
  最多抓一次（再点会直接用刚抓到的数据），每个 IP 每小时最多刷新 30 次；抓取失败会保留原来的价格。
- **中英双语界面**，用 8 位「清单码」在多台设备间同步，不用注册。

## 运行要求

- **澳洲 IP 地址**（见上面的警告）。
- Python 3.9+ 和系统自带的 `curl`（Coles 会拦截 Python 自带的 HTTP 客户端，但放行 `curl`）。不需要安装任何第三方包。
- 或者直接用 Docker。

## 本地运行

```bash
python3 server.py
```

打开 http://localhost:8765 。macOS 上也可以双击 `启动比价.command`。

所有数据（包括价格缓存）都保存在 `./data/app.db`，重启程序不会重新抓取价格。在同一个价格周内
（周三 7:00 到下周三）只读取已经保存的价格；新的一周第一次打开时，只会更新你**已选择的货品**
（当前清单和每周必需品）的价格，其他搜索词只有你再去搜的时候才会查。

## 部署

服务器需要满足三点：**澳洲 IP**、**把 `/data` 挂载成持久化存储**（否则每次重新部署，用户的清单和价格缓存都会被清空）、
**进程一直在线**（周三的更新任务跑在服务器进程里，会休眠的服务会推迟执行）。

### 用 Docker 部署在澳洲的服务器（推荐）

任何位于澳洲的云服务器（悉尼、墨尔本等）都可以。

```bash
git clone https://github.com/Eretouching/coles-vs-woolies.git
cd coles-vs-woolies
docker build -t coles-vs-woolies .
docker run -d --name price-check --restart unless-stopped \
  -p 8080:8080 -v price-check-data:/data \
  --env-file .env \
  coles-vs-woolies
```

可选设置（邮件等）参考 [`.env.example`](.env.example)，复制成 `.env` 即可。前面放一个带 HTTPS 的反向代理
（Caddy、nginx 等）。健康检查：`GET /healthz`。

### Zeabur 等容器平台

只有平台能把服务放在**澳洲区域**才适用，开始前请先确认。部署后打开
`/api/search?store=woolworths&q=milk` 和 `/api/search?store=coles&q=milk`：能看到商品 JSON 就说明可用；
返回 `error`，说明平台的 IP 被拦了。

1. 用你 fork 的仓库新建服务，会自动识别 `Dockerfile`。
2. 添加**存储卷**：Volume ID 填 `data`，Mount Directory 填 `/data`（Zeabur：服务页面 → Volumes）。
   挂载存储卷后服务不支持无停机重启，每次重启会有短暂中断，数据会保留。没挂的话，启动日志里会有警告。
3. 暴露端口 `8080` 并生成域名。
4. 按需添加下面的环境变量。

## 配置

所有环境变量都是可选的，参考 [`.env.example`](.env.example)。

| 变量 | 默认值 | 说明 |
|---|---|---|
| `HOST` | `127.0.0.1`（Docker 镜像里是 `0.0.0.0`） | 监听地址 |
| `PORT` | `8765`（Docker 镜像里是 `8080`） | 监听端口 |
| `DATA_DIR` | `./data`（Docker 镜像里是 `/data`） | `app.db` 所在目录，生产环境必须是持久化存储 |
| `WEEKLY_REFRESH` | `selected`（Docker 镜像里是 `all`） | 周三任务更新哪些价格。`selected`：只更新每个用户当前清单和每周必需品；`all`：再更新过去三周搜过的所有词，让大家打开都是秒出结果（适合多人共用的服务器） |
| `SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASS`、`SMTP_FROM` | – | 每周特价邮件的发件设置。不设置 `SMTP_HOST` 和 `SMTP_USER` 就只能在网页里看特价。587 = STARTTLS，465 = SSL，Gmail 需要用「应用专用密码」 |
| `APP_URL` | – | 邮件里的链接 |
| `COLES_BFF_KEY` | 自动读取 | Coles 门店搜索用的网页公开 key。只有 Coles 网页读不到时才需要手动设置：打开 coles.com.au，在浏览器控制台运行 `__RUNTIME_CONFIG__.BFF_API_SUBSCRIPTION_KEY` |

## 运维

- **每周任务**：每周三悉尼时间 7:00 起（或新的一周第一次启动程序时），服务器慢慢重新查价
  （Coles 请求间隔 5 秒，Woolworths 间隔 2 秒）：先更新每周必需品，再更新各人当前清单，然后发特价邮件，
  最后（仅 `WEEKLY_REFRESH=all`）更新其他被搜过的词。被 Coles 拦截就暂停 15 分钟再试，没更新完的 1 小时后补跑。
- **备份**：所有数据都在 `$DATA_DIR/app.db`（SQLite，WAL 模式）。用 `sqlite3 app.db ".backup backup.db"` 备份，
  或者停掉服务后把 `app.db`、`app.db-wal`、`app.db-shm` 一起复制走。
- **升级**：拉取新代码、重新构建、重启即可，数据库新增的字段会自动补上。
- **日志**：接口请求和每周任务的进度都输出到标准输出。

## 常见问题

| 现象 | 原因 / 解决办法 |
|---|---|
| 所有价格查询都返回 502 | 服务器不在澳洲 IP 上，把服务迁到澳洲 |
| 只有 Coles 失败，提示 blocked by Coles anti-bot | 暂时的。Coles 限速，服务器会暂停 Coles 请求 10 分钟，稍后再试 |
| Coles 门店搜索失败 | 设置 `COLES_BFF_KEY`（见上面） |
| 重新部署后清单消失 | `/data` 没有挂载持久化存储 |
| 收不到特价邮件 | 没设置 `SMTP_HOST`/`SMTP_USER`、用户没开启提醒，或者周三服务在休眠 |
| 一键加购提示「请先登录」 | 先在超市官网登录，再点一次书签。超市网站改版后，书签可能需要更新 |

## 工作原理

| 文件 | 作用 |
|---|---|
| `server.py` | HTTP 服务器、JSON 接口、按 IP 限速 |
| `stores.py` | 访问 Coles 和 Woolworths（Woolworths 用 JSON 搜索接口；Coles 用 Next.js 数据接口，通过 `curl` 访问） |
| `db.py` | SQLite：用户（清单码）、清单、必需品、选品记忆、设置 |
| `pricecache.py` | 每周价格缓存，有效期到下一个周三悉尼时间 7:00 |
| `weekly.py` | 周三任务：慢慢更新价格、检查特价、发邮件 |
| `static/` | 网页（`app.js`、`app.css`、`dict.js` 中文→英文搜索词表） |
| `static/cart-bookmarklet.js` | 「一键加购」书签的源码（在超市网站上运行） |

<details>
<summary>接口列表</summary>

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/search?store=coles\|woolworths&q=&storeId=&fresh=1` | 搜索商品（`storeId` 是 Coles 门店编号，可选；`fresh=1` 实时抓取，有限频） |
| GET | `/api/stores?q=2067` | 按邮编/区名找附近的 Coles 门店 |
| POST | `/api/users` | 新建清单码 |
| GET | `/api/users/{code}` | 读取清单、必需品和设置 |
| PUT | `/api/users/{code}/list` · `/essentials` · `/picks` · `/settings` | 保存 |
| GET | `/api/users/{code}/specials` | 检查必需品本周的特价 |
| POST | `/api/users/{code}/test-email` | 立即发一封特价邮件 |
| GET | `/healthz` | 健康检查 |

</details>

## 隐私与安全

- 服务器按清单码保存：购物清单、必需品、记住的商品选择、Coles 门店、语言，以及（仅当你填写时）你的邮箱。
  不会接触任何密码或超市账号。
- **知道清单码的人可以查看和修改这份清单**，请像密码一样保管，不要公开发布。
- 限速是按客户端 IP 计算的。放在反向代理后面时，请确认代理会设置 `X-Forwarded-For`，并且应用端口不能从公网直接访问。

## 免责声明

这是一个独立的非官方项目，**与 Coles Group、Woolworths Group 没有任何关联，也未获得它们的认可**。它读取的是
你在浏览器里同样能看到的公开商品页面，但两家的使用条款可能限制自动化访问，请负责任地使用：仅限个人或小范围使用，
不要做高频批量抓取，并保留内置的每周缓存。实体店价格可能不同；超市网站改版后，本工具随时可能失效。
按现状提供，不作任何担保。

## 参与贡献

欢迎提交 Issue 和 Pull Request，尤其是超市网站改版之后的修复。代码有意不使用任何第三方依赖，请保持这一点。
提交前可以先检查：`python3 -m py_compile *.py` 和 `node --check static/app.js static/cart-bookmarklet.js`。

## 许可证

[MIT](LICENSE)
