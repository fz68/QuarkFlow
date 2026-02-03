# Phase 5: 夸克转存实现 - 抓包指导

## 目标
找到夸克网盘"转存到我的网盘"的 API 接口和请求格式。

## 抓包步骤

### 1. 准备工具
- Chrome/Edge 浏览器
- 已登录夸克网盘账号

### 2. 打开开发者工具
1. 按 F12 打开开发者工具
2. 切换到 "Network"（网络）标签
3. 勾选 "Preserve log"（保留日志）
4. 在过滤器中输入 `pan.quark.cn`

### 3. 执行转存操作
1. 访问任意夸克分享链接（例如：`pan.quark.cn/s/xxxxxx`）
2. 点击"保存到我的云盘"按钮
3. 在弹出的对话框中确认保存

### 4. 记录关键信息

**查找以下请求：**
```
/comm/savetask   或
/clip/save      或
/saveto         或
/clouddrive/file/sort
```

**需要记录的详细信息：**

#### 请求 URL
```
完整 URL: https://pan.quark.cn/xxxx/xxxx
```

#### 请求方法
```
POST 或 GET
```

#### Request Headers（关键）
```
Cookie: （完整 Cookie，包括 _uutt, _puutt 等字段）
User-Agent: （浏览器 UA）
Referer: （来源页面）
Content-Type: application/json 或其他
```

#### Request Payload（如果有的话）
```json
{
  "fids": "文件ID",
  "to_pdir_fiid": "目标目录ID",
  ...
}
```

#### Response 响应
```json
{
  "data": {...},
  "errno": 0,
  "errmsg": "success"
}
```

### 5. 重点提取

**从 Cookie 中提取：**
```
QUARK_COOKIE = "_uutt=xxxxx; _puutt=yyyyy; ..."
```

**从链接中提取：**
```
share_id: pan.quark.cn/s/<share_id> 中的字符串
```

**可选：folder_id**
```
如果想保存到特定目录，记录目标目录的 folder_id
```

## 示例格式（参考）

请按以下格式记录抓包结果：

```
=== 夸克转存 API 抓包记录 ===

URL: https://pan.quark.cn/xxxx/xxxx
Method: POST

Headers:
Content-Type: application/json
Cookie: [完整 Cookie]
User-Agent: [浏览器 UA]
Referer: https://pan.quark.cn/s/xxxxx

Payload:
{
  "share_id": "xxxxx",
  ...
}

Response:
{
  "data": {...},
  "errno": 0
}
```

## 完成后
将抓包结果发送给我，我会据此实现 Python 代码。
