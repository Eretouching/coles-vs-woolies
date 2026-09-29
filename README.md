# Coles vs Woolworths 比价 · Price Check

输入购物清单（中文或英文），实时比较 Coles 和 Woolworths 网上商城的价格。

- **比价**：整单去哪家便宜、每件哪家便宜（按单价比，自动算 "2 for $X" 多买优惠）、两家分开买能省多少
- **每周必需品**：点商品名左边的 ☆ 标记每周都买的东西（会记住两边选好的具体商品），下周点「开始新一周」一键载入
- **本周特价提醒**：两家超市每周三换特价。「本周特价」页显示你的必需品有哪些在打折；配置了邮箱发件服务器的话，每周三早上 7 点（悉尼时间）自动发邮件
- **中英双语**：右上角切换
- **多设备同步**：不用注册。每个浏览器会自动得到一个 8 位「清单码」，在手机上输入同一个码就能看到同一份清单

## 本地运行

双击 `启动比价.command`，或在终端运行：

```bash
python3 server.py
```

然后打开 http://localhost:8765 。只需要 Python 3.9+ 和系统自带的 curl，不用装任何第三方包。

## 部署到 Zeabur

1. 把这个文件夹推到 GitHub（`data/` 已在 `.gitignore` 里，不会上传本地数据库）。
2. Zeabur 控制台 → 新建项目（**区域尽量选离澳洲近的**，例如新加坡/东京）→ 添加服务 → 选 GitHub 仓库。
   Zeabur 会自动识别 `Dockerfile` 并构建。
3. **挂载持久化存储**：服务的「Volumes / 硬盘」里添加一个，挂载路径填 `/data`。
   不挂载的话，每次重新部署数据库都会被清空。
4. 「Networking / 网络」里生成一个域名，端口是 `8080`。
5. （可选）开启邮件提醒，在「Variables / 环境变量」里加上：

   | 变量 | 例子 | 说明 |
   |---|---|---|
   | `SMTP_HOST` | `smtp.gmail.com` | 发件服务器 |
   | `SMTP_PORT` | `587` | 587（STARTTLS）或 465（SSL） |
   | `SMTP_USER` | `you@gmail.com` | 登录用户名 |
   | `SMTP_PASS` | 应用专用密码 | Gmail 需要在账号安全设置里生成「应用专用密码」 |
   | `SMTP_FROM` | `Price Bot <you@gmail.com>` | 可选，默认同 `SMTP_USER` |
   | `APP_URL` | `https://xxx.zeabur.app` | 邮件里的链接 |

   也可以用 Resend、Brevo、SendGrid 等服务提供的 SMTP。

部署完先打开 `https://你的域名/api/search?store=coles&q=milk` 和 `...store=woolworths&q=milk`，
能看到商品 JSON 就说明服务器能正常访问两家超市。

## 文件结构

| 文件 | 作用 |
|---|---|
| `server.py` | HTTP 服务器和 API |
| `stores.py` | 查询 Coles / Woolworths 商品价格 |
| `db.py` | SQLite 数据库（`$DATA_DIR/app.db`） |
| `weekly.py` | 每周特价检查和邮件提醒 |
| `static/` | 网页（`app.js` 逻辑、`dict.js` 中文→英文词表、`app.css` 样式） |

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/search?store=coles\|woolworths&q=` | 搜索商品 |
| POST | `/api/users` | 新建清单码 |
| GET | `/api/users/{code}` | 读取清单、必需品和设置 |
| PUT | `/api/users/{code}/list` · `/essentials` · `/settings` | 保存 |
| GET | `/api/users/{code}/specials` | 本周必需品特价检查 |
| POST | `/api/users/{code}/test-email` | 立即发一封特价提醒邮件 |
| GET | `/healthz` | 健康检查 |

## 说明

- 价格来自两家官网网上商城的默认门店，实体店偶尔不同。
- Coles 网站有防爬虫。如果提示被拦截，过几分钟再刷新即可。
- 清单码就是访问凭证，知道码的人都能看到和修改这份清单。
- 这是个人/小范围使用的工具，请不要高频批量抓取。
