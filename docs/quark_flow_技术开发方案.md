# QuarkFlow 技术开发方案

## 1. 项目背景

用户每天从 Telegram 无损音乐分享频道 **@D_wusun** 获取分享内容。频道中的内容通常为 **夸克网盘分享链接**。当前流程为：

1. 人工查看 Telegram 频道更新
2. 点击夸克网盘链接
3. 保存到个人夸克网盘
4. 在夸克网盘内将文件/目录移动到指定归档目录

该流程重复性高、人工成本大，具备明确的自动化条件。

**QuarkFlow** 旨在通过一个常驻 Docker 服务，实现上述流程的全自动化。

---

## 2. 项目目标

- 自动监听 Telegram 频道 @D_wusun 的新消息
- 精准提取消息中的夸克网盘分享链接
- 自动完成夸克网盘「转存到个人空间」操作
- 按预设规则，将文件/目录移动到指定目标目录
- 支持 Docker 部署，长期稳定运行

非目标（v1 阶段不做）：
- 音频格式转换 / 重命名 / 元数据整理
- 多网盘支持
- Web UI 管理界面

---

## 3. 总体架构

```
Telegram Channel (@D_wusun)
        │
        ▼
Telegram Listener (含链接提取)
        │
        ▼
    SQLite DB
        │
        ▼
Worker (轮询 pending 任务)
        │
        ▼
Quark Automation Service
```

采用 **单容器简化架构**，直接通过 DB 耦合，无需内存队列。

---

## 4. 推荐技术栈（最终定案）

### 4.1 核心技术

| Category | Technology | Notes |
|----------|-----------|-------|
| **Language** | Python 3.11 | 稳定版本，完整 async 支持 |
| **Async Framework** | asyncio | 内置，无额外依赖 |
| **Telegram Client** | Telethon | 官方 API，用户账号模式 |
| **HTTP Client** | httpx | 现代异步 HTTP 库 |
| **Database** | SQLite | 轻量级，本地持久化（同步访问） |
| **Container** | Docker + Docker Compose | 标准化部署 |

---

## 5. 工程级最佳实践

### 5.1 ✅ 必做

- **网络 IO async**（Telegram、夸克 API）
- **数据库同步**（SQLite 单连接足够）
- **状态先写 DB，再做动作**（幂等性保证）

- **所有状态先写 DB，再做动作**
  - 幂等性保证
  - 防止重复处理

- **单实例运行（不要 scale）**
  - 简化架构
  - 避免并发冲突

### 5.2 ❌ 不要做

- **不要"先请求再去重"**
  - 先查 DB，再决定是否处理

- **不要"转存成功再写状态"**
  - 先写 pending，再执行，最后更新结果

- **不要用 cron + 脚本拼凑**
  - 常驻服务，事件驱动

---

## 6. QuarkFlow 实际开发步骤规划（实战版）

### 6.1 总体原则（先看）

1. **每一步都能单独运行**
2. **每一步都有可验证结果**
3. **先 Telegram，后夸克**
4. **先去重，后自动化**

---

### 6.2 Phase 0：准备阶段（0.5 天）

#### 0.1 项目初始化

```bash
mkdir quarkflow
cd quarkflow
git init
```

#### 0.2 目录结构（第一版）

```
quarkflow/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ db.py
│  ├─ telegram/
│  ├─ quark/
│  ├─ tasks/
│  └─ utils/
├─ data/           # SQLite / logs
├─ Dockerfile
├─ docker-compose.yml
└─ requirements.txt
```

#### 0.3 明确"成功标准"

- Docker 启动后，不报错，持续运行

---

### 6.3 Phase 1：SQLite + 去重核心（1 天）🔥

> 这是整个项目的地基

#### 1.1 建表（直接照方案）

- `tg_messages`
- `quark_shares`

#### 1.2 写 DAO（同步即可）

功能最少化：

- `insert_tg_message()`
- `insert_share_pending()`
- `mark_share_saved()`
- `mark_share_failed()`

#### 1.3 写一个测试脚本

```bash
python app/db_test.py
```

**验证**：
- 重复 insert 会被拒绝
- status 正确变化

**产出**：你已经有"不会重复"的系统骨架

---

### 6.4 Phase 2：Telegram Listener（1 天）✅

#### 2.1 Telethon 登录

- 用用户账号
- 首次人工扫码

#### 2.2 只做一件事

监听 @D_wusun，打印消息文本

```
[TELEGRAM] new message id=12345
```

#### 2.3 接入第一层去重

- `message_id` 已存在 → 不打印

#### 2.4 只提取链接，不做任何转存

```
[LINK] found pan.quark.cn/s/abcd
```

**产出**：
- Telegram 连通
- 不重复打印
- 可长期运行

---

### 6.5 Phase 3：链接提取 + share_id 去重（0.5 天）

#### 3.1 在 TelegramListener 中添加链接提取

- regex 提取 `pan.quark.cn/s/xxxx`
- 标准化 `share_id`

#### 3.2 接入第二层去重

- `share_id` 已存在 → log skip

```
[DEDUP] share_id=abcd skip
```

#### 3.3 验证完整流程

- 新消息 → 提取链接 → 写 DB pending
- 查询 DB 确认 pending 状态正确

**产出**：任意重复链接不会再进入任务

---

### 6.6 Phase 4：Worker 简化实现（0.5 天）

#### 4.1 直接从 DB 轮询 pending 任务

```python
# 伪代码
while True:
    tasks = db.get_pending_tasks(limit=5)
    for task in tasks:
        await process_task(task)
    await asyncio.sleep(10)
```

#### 4.2 限流控制

```python
sem = asyncio.Semaphore(1)  # 同时只处理 1 个任务
```

#### 4.3 模拟转存

```
[WORKER] processing share_id=abcd (mock)
[WORKER] done, status=saved
```

**产出**：流程完整跑通（假转存）

---

### 6.7 Phase 5：夸克"转存"最小实现（2 天）⚠️ 最难

#### 5.1 先手工抓包（不写代码）

- 浏览器转存一次
- 找关键接口
- 记录 headers / payload

> ⚠️ 这一阶段别急着写代码

#### 5.2 Python 复现 HTTP 请求

- Cookie 硬编码（先）
- 成功返回即算过关

```
[QUARK] saved share_id=abcd
```

#### 5.3 成功后立即：

- 写 DB：status=saved
- 保存 file_id

#### ❌ 不要做移动目录

**产出**：真正完成自动转存

---

### 6.8 Phase 6：目录移动（可选，0.5–1 天）

> ⚠️ **非 v1 核心，可后置实现**

#### 6.1 抓"移动目录"接口

- `file_id → target_folder_id`

#### 6.2 封装 FolderOrganizer

```
[MOVE] abcd -> /音乐/无损/@D_wusun
```

#### 6.3 失败可接受（不影响转存）

**产出**：自动归档完成（或手动归档）

---

### 6.9 Phase 7：Docker 化（0.5 天）

#### 7.1 Dockerfile

**轻量化优先**（NAS 环境友好）：
- `python:3.11-slim`（~130 MB）
- 仅安装核心依赖：telethon, httpx
- 多架构支持：`linux/amd64`, `linux/arm64`

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

VOLUME /data
CMD ["python", "-m", "app.main"]
```

**镜像说明**：
- 基础镜像：~130MB
- 多架构支持：`linux/amd64`, `linux/arm64`

#### 7.2 docker-compose

- volume 挂载 /data
- env 注入 cookie
- 资源限制（可选）：

```yaml
services:
  quarkflow:
    build: .
    volumes:
      - ./data:/data
    env_file: .env
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M
```

#### 7.3 验证

```bash
docker compose up -d
docker logs -f quarkflow
```

---

### 6.10 Phase 8：兜底 & 稳定性（1 天）

#### 8.1 异常重试

- `failed` → 次日再试

#### 8.2 Cookie 失效检测

- 特定错误码 → log 提醒

#### 8.3 限流

- 每次转存 sleep 5–10s

---

## 7. 技术选型（原有内容，保留参考）

### 4.1 运行环境

- Docker + Docker Compose
- Python 3.11
- Linux (Alpine / Debian slim)

### 4.2 Telegram 监听

- 使用 **Telegram 官方 API（非 Bot）**
- 库：`Telethon`

原因：
- 私有频道/受限频道可读性更好
- 消息结构完整，便于解析链接

### 4.3 任务与状态存储

- SQLite（本地）
- 用于：
  - 已处理消息 ID 去重
  - 已转存链接记录
  - 错误重试状态

### 4.4 夸克网盘自动化

> 夸克网盘暂无公开稳定 API

方案：

- 使用 **Cookie + httpx 请求模拟**

功能点：
- 转存到个人网盘
- 获取转存后文件/目录 ID
- 执行移动操作（可选）

**为什么不用 Playwright**：
- 资源占用大（~500MB），NAS 环境不友好
- httpx + Cookie 足够应对，无需无头浏览器

### 4.5 日志与监控

- Python `logging`
- 日志分级：INFO / WARNING / ERROR
- 文件日志 + stdout（Docker）

---

## 5. 核心模块设计（简化版）

### 5.1 TelegramListener

职责：
- 登录 Telegram 账号
- 监听频道 @D_wusun 新消息
- 提取夸克网盘链接（regex）
- 将链接直接写入 DB（pending 状态）

关键点：
- 只处理包含 `pan.quark.cn` 的消息
- 按 message_id 去重（第一层）
- 标准化 share_id（第二层）

实现：
```python
# 伪代码
async def on_new_message(message):
    if not contains_quark_link(message.text):
        return

    # 第一层去重：Telegram 消息
    if not db.insert_tg_message(message.id):
        return  # 已处理

    # 提取并标准化 share_id
    share_id = extract_share_id(message.text)

    # 第二层去重：share_id
    if not db.insert_share_pending(share_id):
        return  # 已存在

    logger.info(f"[NEW] share_id={share_id}")
```

---

### 5.2 Worker

职责：
- 从 DB 轮询 pending 任务
- 调用 QuarkClient 执行转存
- 更新任务状态

实现：
```python
# 伪代码
sem = asyncio.Semaphore(1)  # 限流：同时只处理 1 个任务

async def worker():
    while True:
        async with sem:
            task = db.get_pending_task()
            if task:
                await process_task(task)
        await asyncio.sleep(5)  # 轮询间隔
```

---

### 5.3 QuarkClient

职责：
- 模拟登录夸克网盘（Cookie）
- 执行「保存到我的网盘」
- 返回保存后的文件/目录 ID

实现：
- httpx + Cookie 硬编码
- 必要时记录请求日志用于调试

安全策略：
- Cookie 通过 `.env` 注入
- 不在日志中输出敏感信息

---

### 5.4 FolderOrganizer（可选，非 v1 核心）

职责：
- 将新转存的目录移动到指定归档目录

示例规则：
```
/我的网盘/音乐/无损/@D_wusun/
```

**注意**：
- v1.0 可不实现，手动归档即可
- 失败不影响核心转存功能
- 后续有需求再实现

---

## 6. Docker 设计

### 6.1 Dockerfile（概念）

- Base: python:3.11-slim
- 安装依赖：telethon, requests, playwright
- 挂载：
  - `/data`（SQLite + 日志）

### 6.2 环境变量

```env
TG_API_ID=
TG_API_HASH=
TG_SESSION=
QUARK_COOKIE=
TARGET_FOLDER_ID=
```

---

## 7. 去重与幂等设计（核心）

QuarkFlow 的稳定性依赖**两层去重策略**，覆盖主要重复场景。

---

### 7.1 第一层：Telegram 消息级去重

**目标**：保证同一条频道消息只被处理一次。

**关键字段**：
- `channel_id`
- `message_id`

**数据表设计**：
```sql
CREATE TABLE tg_messages (
  channel_id TEXT,
  message_id INTEGER,
  processed_at DATETIME,
  PRIMARY KEY (channel_id, message_id)
);
```

**处理规则**：
- 新消息到达时尝试插入
- 主键冲突则视为已处理，直接丢弃

**解决问题**：
- Docker 容器重启
- Telegram 重推事件
- 历史消息重复扫描

---

### 7.2 第二层：夸克分享链接级去重（核心层）

**目标**：防止同一夸克分享链接被多次转存。

#### 7.2.1 链接标准化

无论原始链接形式如何，统一解析为：

```
share_id = {pan.quark.cn/s/<share_id>}
```

忽略所有 query 参数（如提取码）。

---

#### 7.2.2 分享链接状态表

```sql
CREATE TABLE quark_shares (
  share_id TEXT PRIMARY KEY,
  first_seen DATETIME,
  status TEXT, -- pending / saved / failed
  file_id TEXT,
  last_error TEXT
);
```

**状态含义**：
- `pending`：已发现链接，正在或即将处理
- `saved`：已成功转存
- `failed`：处理失败，可按策略重试

**处理规则**：
1. 提取 `share_id`
2. 尝试插入状态为 `pending`
3. 若已存在：
   - `saved` → 直接跳过
   - `failed` → 按重试策略处理
   - `pending` → 认为已有任务在处理，跳过

**注意**：只要 SQLite 事务正确执行，不会出现"转存成功但状态丢失"的情况，无需第三层兜底。

---

### 7.3 去重决策完整流程

```
收到 Telegram 消息
   │
   ▼
[消息ID 是否已处理] —— 是 → 丢弃
   │否
   ▼
提取并标准化 share_id
   │
   ▼
[share_id 是否存在]
   ├─ status = saved   → 跳过
   ├─ status = pending → 跳过
   ├─ status = failed  → 按策略重试
   └─ 不存在          → 创建 pending 任务
           │
           ▼
      执行夸克转存
           │
           ▼
   成功 → status=saved + file_id
   失败 → status=failed + error
```

---

### 7.5 工程实现约束（必须遵守）

- 所有状态写入必须在事务中完成
- `pending` 状态必须先于实际转存写入（防并发）
- SQLite 数据库必须挂载到 Docker volume
- 日志中明确标识去重行为：
  ```
  [DEDUP] share_id=xxxx already saved, skip
  ```

---

## 8. 运行流程（时序）

1. Docker 容器启动
2. TelegramListener 登录并开始监听
3. 新消息到达 @D_wusun
4. 提取夸克分享链接
5. 创建转存任务
6. QuarkClient 执行转存
7. FolderOrganizer 移动目录
8. 记录成功状态

---

## 9. 风险与应对

| 风险 | 应对策略 |
|----|----|
| 夸克接口变动 | 模块化封装，记录请求日志便于调试 |
| Telegram 限流 | 控制请求频率，Telethon 内置限流 |
| Cookie 失效 | 日志告警 + 快速更新机制（docker restart） |
| 重复转存 | 两层去重 + SQLite 事务保证 |
| NAS 资源限制 | 轻量化镜像（~150MB），内存限制 256MB |

---

## 10. 服务器部署说明

### 10.1 支持的环境

**推荐部署方式**：
- 云 VPS（Vultr、DigitalOcean、Linode 等）
- 独立服务器
- 虚拟机

**支持的架构**：
- `linux/amd64`：x86_64 服务器（主流）
- `linux/arm64`：ARM 服务器（如 Oracle Cloud ARM）

**最低配置建议**：
- 内存：512MB（推荐 1GB）
- 存储：1GB（Docker 镜像 + 数据 + 日志）
- 网络：稳定外网连接

**网络要求**：
- ✅ Telegram：可直连（国外服务器无障碍）
- ⚠️ 夸克网盘：可能需要代理（详见下方说明）

---

### 10.2 夸克网盘访问说明

**问题**：夸克网盘主要服务国内用户，国外服务器访问可能受限或速度慢。

**解决方案**（按优先级）：

#### 方案 1：服务器有回国代理（推荐）

如果服务器已有代理服务（如 v2ray、trojan），配置容器使用：

```yaml
# docker-compose.yml
services:
  quarkflow:
    build: .
    volumes:
      - ./data:/data
    env_file: .env
    environment:
      # 使用宿主机代理
      - HTTP_PROXY=http://172.17.0.1:7890
      - HTTPS_PROXY=http://172.17.0.1:7890
    restart: unless-stopped
```

#### 方案 2：使用夸克海外 CDN

部分夸克 API 可能支持海外访问，先尝试直连，如失败再考虑代理。

#### 方案 3：混合部署（高级）

- Telegram 监听：部署在国外服务器
- 夸克转存：部署在国内 NAS/服务器
- 通过消息队列（如 Redis）解耦

**v1.0 建议**：先尝试方案 1，如服务器无代理则考虑方案 3。

---

### 10.3 Docker Compose 配置

```yaml
# docker-compose.yml
services:
  quarkflow:
    build: .
    container_name: quarkflow
    volumes:
      - ./data:/data
    env_file: .env
    restart: unless-stopped
    # 可选：日志大小限制
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

### 10.4 环境变量配置

创建 `.env` 文件：

```env
# Telegram 配置
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash
TG_CHANNEL=@D_wusun

# 夸克网盘配置
QUARK_COOKIE="your_quark_cookie"

# 可选：代理配置（仅夸克访问需要）
# HTTP_PROXY=http://172.17.0.1:7890
# HTTPS_PROXY=http://172.17.0.1:7890

# 可选：目标目录
# TARGET_FOLDER_ID=/音乐/无损/@D_wusun
```

---

### 10.5 部署步骤

#### 首次部署

```bash
# 1. 克隆项目（或上传代码）
git clone <repo_url>
cd quarkflow

# 2. 配置环境变量
cp .env.example .env
vim .env  # 填入 API ID/Hash 和 Cookie

# 3. 构建并启动
docker compose up -d

# 4. 查看日志，等待扫码登录
docker logs -f quarkflow

# 5. 扫码完成后，容器自动开始监听
```

#### 日常管理

```bash
# 查看实时日志
docker logs -f quarkflow

# 重启容器
docker compose restart

# 停止服务
docker compose down

# 更新代码后重新部署
git pull
docker compose up -d --build

# 进入容器调试
docker exec -it quarkflow bash
```

---

### 10.6 监控与维护

#### 日志管理

```bash
# 实时查看日志
docker logs -f quarkflow

# 查看最近 100 行日志
docker logs --tail 100 quarkflow

# 查看特定时间段日志
docker logs --since 1h quarkflow
```

#### 数据库查询

```bash
# 进入容器
docker exec -it quarkflow bash

# 查询任务状态
sqlite3 /data/quarkflow.db "SELECT share_id, status, first_seen FROM quark_shares ORDER BY first_seen DESC LIMIT 10;"

# 统计各状态任务数
sqlite3 /data/quarkflow.db "SELECT status, COUNT(*) FROM quark_shares GROUP BY status;"
```

#### Cookie 更新

```bash
# 1. 编辑 .env 文件
vim .env

# 2. 重启容器使配置生效
docker compose restart

# 3. 验证日志中无 Cookie 相关错误
docker logs --tail 20 quarkflow
```

#### 备份数据

```bash
# 备份数据库
docker cp quarkflow:/data/quarkflow.db ./backup/quarkflow_$(date +%Y%m%d).db

# 备份 session 文件
docker cp quarkflow:/data/app.session ./backup/
```

---

### 10.7 故障排查

#### 问题 1：Telegram 连接失败

**症状**：日志显示 `ConnectionError` 或超时

**解决**：
```bash
# 检查服务器网络
ping api.telegram.org

# 检查防火墙规则
sudo ufw status  # Ubuntu
sudo iptables -L  # CentOS
```

#### 问题 2：夸克转存失败

**症状**：日志显示 `Cookie expired` 或 `403 Forbidden`

**解决**：
- 更新 `.env` 中的 `QUARK_COOKIE`
- 如服务器在国外，配置代理访问夸克

#### 问题 3：容器频繁重启

**症状**：`docker ps` 显示 `Restarting` 状态

**解决**：
```bash
# 查看详细错误日志
docker logs --tail 50 quarkflow

# 检查内存使用
docker stats quarkflow
```

---

## 11. 部署检查清单

### 11.1 部署前准备

- [ ] 服务器已安装 Docker + Docker Compose
- [ ] 已创建项目目录并上传代码
- [ ] 已创建 `data/` 目录用于持久化
- [ ] 已配置 `.env` 文件（TG_API_ID, TG_API_HASH, QUARK_COOKIE）
- [ ] （可选）服务器有代理服务（如需访问夸克）

### 11.2 首次启动验证

```bash
# 1. 构建镜像
docker compose build

# 2. 启动容器
docker compose up -d

# 3. 确认容器运行
docker ps | grep quarkflow

# 4. 查看日志，等待扫码登录
docker logs -f quarkflow
# 出现 "Please enter your phone code" 时，用手机 Telegram 扫码

# 5. 扫码成功后，看到 "Listening for messages..." 即可
```

### 11.3 运行状态检查

```bash
# 检查容器是否持续运行（无频繁重启）
docker ps

# 查看最新日志，确认无错误
docker logs --tail 20 quarkflow

# 验证 Telegram 连接正常
# 日志中应出现 "Listening for updates..."

# 验证数据库正常
docker exec -it quarkflow sqlite3 /data/quarkflow.db "SELECT COUNT(*) FROM tg_messages;"
```

### 11.4 监控告警（可选）

**简单监控脚本**：

```bash
#!/bin/bash
# check_quarkflow.sh

if ! docker ps | grep -q quarkflow; then
    echo "ALERT: quarkflow container is not running!"
    # 发送通知（如邮件、Telegram bot）
fi

# 检查最近是否有错误日志
if docker logs --since 1h quarkflow | grep -i "error"; then
    echo "WARNING: Errors found in recent logs"
fi
```

加入 crontab：
```bash
# 每 10 分钟检查一次
*/10 * * * * /path/to/check_quarkflow.sh
```

---

## 12. 后续可扩展方向

- 多 Telegram 频道支持
- 文件名 / 专辑自动整理
- 音乐元数据抓取（FLAC / APE）
- 简易 Web UI（可选，NAS 环境非必需）
- 多网盘（阿里云盘 / 百度网盘）

---

## 13. 项目定位总结

**QuarkFlow** 是一个：

> 面向个人高频使用场景的、稳定、低维护成本的
> Telegram → 夸克网盘自动化归档流水线

强调：
- 实用性优先，不追求过度工程化
- 自动化完整闭环
- Docker 化，支持 VPS/NAS 部署
- 可长期无人值守运行

