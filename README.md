# QuarkFlow

> Telegram → 夸克网盘自动化归档工具

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

QuarkFlow 是一个轻量级的自动化工具，实时监听 Telegram 频道中的夸克网盘分享链接，并自动转存到个人网盘。

## ✨ 核心特性

- 🎯 **实时监听** - 事件驱动，无需轮询
- 🛡️ **两层去重** - Telegram 消息级 + 夸克链接级去重
- ⚡ **异步架构** - asyncio 高性能处理
- 🐳 **Docker 部署** - 一键启动，支持 amd64/arm64
- 📦 **轻量简洁** - ~150MB 镜像，专注核心功能
- 🔄 **状态追踪** - SQLite 持久化，幂等性保证
- 🔔 **智能告警** - Cookie 过期自动 Telegram 通知
- 🌐 **WebUI 配置** - 可视化界面，无需手动编辑文件

## 🏗️ 架构

```
Telegram (@D_wusun)
  ↓ [实时监听]
TelegramListener
  ↓ [提取链接 + 去重]
SQLite Database
  ↓ [Worker 轮询]
QuarkClient
  ↓ [获取 stoken + 转存]
夸克网盘 (成功)
```

## 🚀 快速开始

### 1. 环境准备

确保已安装：
- Docker & Docker Compose
- 夸克网盘账号
- Telegram 账号

### 2. 获取 Telegram API 凭证

1. 访问 https://my.telegram.org
2. 登录后点击 "API development tools"
3. 创建应用获取 `api_id` 和 `api_hash`

### 3. 获取夸克网盘 Cookie

1. 登录 https://pan.quark.cn
2. 打开浏览器开发者工具（F12）
3. 切换到 Network 标签
4. 刷新页面，找到任意请求
5. 复制请求头中的完整 Cookie

**关键 Cookie 字段**：
- 必需：`__puus`, `b-user-id`
- 推荐：`kps`, `sign`, `vcode`（用于移动端 API，自动检测）

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# Telegram 配置
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash
TG_CHANNEL=@D_wusun
TG_SESSION=quarkflow

# 夸克网盘配置
# Cookie 应包含：__puus, b-user-id（推荐：kps, sign, vcode）
QUARK_COOKIE="your_complete_cookie_here"

# Worker 配置
WORKER_POLL_INTERVAL=10
WORKER_CONCURRENT_TASKS=1
```

### 5. 启动服务

```bash
docker compose up -d
```

### 6. 查看日志

```bash
docker logs -f quarkflow
```

首次运行会要求扫码登录 Telegram：
1. 日志中会显示手机号输入提示
2. 输入手机号（国际格式，如 +8613800138000）
3. 输入 Telegram 发送的验证码
4. 登录成功后自动开始监听

## 📖 使用说明

### API 策略

QuarkFlow 会自动选择最优 API：
- **移动端 API**（优先）：当 Cookie 包含 `kps`, `sign`, `vcode` 时
- **PC 端 API**（回退）：当缺少移动端参数时

无需手动配置 bx-ua/bx-umidtoken，系统会自动适配。

### 自动化流程

1. **监听阶段**
   - 实时监听 Telegram 频道 @D_wusun
   - 提取夸克网盘分享链接（`pan.quark.cn/s/xxxxx`）
   - 第一层去重：检查 Telegram message_id
   - 第二层去重：检查夸克 share_id
   - 新链接写入数据库（status=pending）

2. **转存阶段**
   - Worker 轮询 pending 任务（每 10 秒）
   - 调用夸克 API 获取 stoken
   - 执行转存操作
   - 更新状态为 saved/failed

3. **状态查询**
   ```bash
   # 进入容器
   docker exec -it quarkflow bash

   # 查询任务状态
   sqlite3 /data/quarkflow.db "SELECT share_id, status, first_seen FROM quark_shares ORDER BY first_seen DESC LIMIT 10;"

   # 统计各状态数量
   sqlite3 /data/quarkflow.db "SELECT status, COUNT(*) FROM quark_shares GROUP BY status;"
   ```

### 数据库状态

- `pending` - 等待处理
- `saved` - 转存成功
- `failed` - 转存失败（可手动重试）

## 🔧 高级配置

### Cookie 获取详细步骤

**方法 1：浏览器开发者工具**

1. 打开 https://pan.quark.cn 并登录
2. 按 F12 打开开发者工具
3. 切换到 "Network" 标签
4. 刷新页面
5. 点击任意请求
6. 在 "Headers" 中找到 "Request Headers"
7. 复制 `Cookie:` 后的完整内容

**方法 2：浏览器扩展**

使用 "Get cookies.txt LOCALLY" 等浏览器扩展导出 Cookie。

**推荐 Cookie 格式**（包含移动端参数）：
```
__puus=xxx; b-user-id=yyy; kps=zzz; sign=www; vcode=vvv; ...
```

如果 Cookie 中包含 `kps`, `sign`, `vcode`，系统会自动使用移动端 API，速度更快且无需额外配置。

### 资源限制

默认限制内存 256MB，可在 `docker-compose.yml` 中调整：

```yaml
deploy:
  resources:
    limits:
      memory: 512M  # 调整为 512MB
```

## 🐳 Docker 部署

### 构建镜像

```bash
docker compose build
```

### 多架构支持

支持 `linux/amd64` 和 `linux/arm64`：

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t quarkflow:latest .
```

### 数据持久化

数据库和日志存储在 `./data` 目录，通过 Docker volume 挂载：

```yaml
volumes:
  - ./data:/data
```

### 日常管理

```bash
# 查看实时日志
docker logs -f quarkflow

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 更新代码后重新部署
git pull
docker compose up -d --build
```

## 🛠️ 开发

### 本地运行

```bash
# 创建 conda 环境
conda create -n quarkflow python=3.11
conda activate quarkflow

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入凭证

# 运行
python -m app.main
```

### 测试

```bash
# 测试数据库去重
python app/db_test.py

# 测试 Worker
python test_worker.py

# 测试夸克转存
python test_quark.py

# 测试完整流程
python test_complete_workflow.py
```

### 项目结构

```
quarkflow/
├── app/
│   ├── main.py                # 主入口
│   ├── config.py              # 配置管理
│   ├── db.py                  # 数据库层
│   ├── telegram/
│   │   └── listener.py        # Telegram 监听器
│   ├── quark/
│   │   └── client.py          # 夸克 API 客户端
│   └── tasks/
│       └── worker.py          # 任务处理器
├── data/                      # SQLite + logs
├── docs/                      # 文档
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🔍 故障排查

### Telegram 连接失败

**症状**：日志显示 `ConnectionError` 或超时

**解决**：
```bash
# 检查网络
ping api.telegram.org

# 检查防火墙
sudo ufw status  # Ubuntu
```

### Cookie 过期自动通知

当检测到 Cookie 过期时，系统会自动发送 Telegram 消息提醒：

```
⚠️ QuarkFlow Cookie 已过期！

错误信息：请先登录

请立即更新：
1. 访问 http://your-vps:8080/login
2. 重新获取 Cookie
3. 重启容器：docker compose restart

Cookie 过期会导致转存失败。
```

**如何更新 Cookie：**

**方式 1：WebUI（推荐）**
1. 浏览器访问 `http://your-vps:8080/login`
2. 按界面提示重新获取并填写 Cookie
3. 重启容器：`docker compose restart`

**方式 2：手动编辑**
```bash
# 1. SSH 到 VPS
ssh user@your-vps

# 2. 编辑 .env 文件
cd QuarkFlow
vim .env

# 3. 更新 QUARK_COOKIE

# 4. 重启容器
docker compose restart
```

### stoken 获取失败

**症状**：`failed to get stoken`

**可能原因**：
- Cookie 过期
- 分享链接需要提取码
- 分享链接已失效

**解决**：
1. 检查 Cookie 是否最新
2. 手动访问分享链接验证

### 容器频繁重启

**症状**：`docker ps` 显示 `Restarting`

**解决**：
```bash
# 查看详细错误
docker logs --tail 50 quarkflow

# 检查内存使用
docker stats quarkflow
```

## 📊 性能优化

### 限流配置

默认同时处理 1 个任务，可在 `.env` 调整：

```env
WORKER_POLL_INTERVAL=5      # 轮询间隔（秒）
WORKER_CONCURRENT_TASKS=1   # 并发任务数
```

### 日志管理

限制日志大小：

```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🔐 安全建议

1. **不要提交敏感信息** - `.env` 文件已在 `.gitignore` 中
2. **定期更新 Cookie** - 夸克 Cookie 会过期
3. **使用强密码** - Telegram 账号开启两步验证
4. **限制容器权限** - 使用非 root 用户运行（可选）

## 📝 更新日志

### v1.1 (最新)
- ✅ 切换到移动端 API（无需 bx-ua/bx-umidtoken）
- ✅ 自动检测 Cookie 中的移动端参数
- ✅ PC 端 API 作为回退方案

### v1.0
- 初始版本
- Telegram 实时监听
- Cookie 过期自动通知
- WebUI 配置界面

## 📝 待办事项

- [ ] Cookie 失效自动检测与告警
- [ ] 失败任务自动重试机制
- [ ] 转存后自动移动到归档目录
- [ ] 多 Telegram 频道支持
- [ ] 简易 Web UI（可选）

## 📄 许可证

MIT License

## 🙏 致谢

- [Telethon](https://github.com/LonamiWebs/Telethon) - Python Telegram 客户端
- [httpx](https://www.python-httpx.org/) - 现代异步 HTTP 客户端
- [quark-auto-save](https://github.com/Cp0204/quark-auto-save) - API 实现参考

## 📮 联系方式

- 提交 Issue：https://github.com/yourusername/QuarkFlow/issues
- 讨论：https://github.com/yourusername/QuarkFlow/discussions

---

**QuarkFlow** - 让 Telegram 音乐分享自动化归档变得简单 🚀
