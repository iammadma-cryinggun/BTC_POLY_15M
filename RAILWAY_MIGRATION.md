# 快速迁移到 Railway - 5分钟指南

## 为什么选择 Railway？

✅ **免费额度**：$5/月信用卡额度
✅ **简单配置**：直接连接 GitHub
✅ **不同 IP**：不受 Zeabur IP 封禁影响
✅ **自动部署**：Git push 自动重新部署
✅ **实时日志**：查看机器人运行状态

---

## 步骤 1: 注册 Railway（1 分钟）

1. 访问：https://railway.app/
2. 点击 "Start Free Trial"
3. 使用 GitHub 账号登录（推荐）
4. 添加支付方式（$5 额度，不会立即扣费）

---

## 步骤 2: 创建新项目（1 分钟）

1. 点击 "New Project" → "Deploy from GitHub repo"
2. 选择仓库：`iammadma-cryinggun/BTC_POLY_15M`
3. Railway 会自动检测到 Dockerfile

---

## 步骤 3: 配置环境变量（2 分钟）

### 必需的环境变量

在 Railway 项目设置中添加：

```bash
# Polymarket 私钥（必需）
POLYMARKET_PK=0xed298792ddcc1e6348a934214fa563324800bfa72ac58fc066ea4ba8a17b1feb

# Proxy 地址（必需 - 你的资金在这个地址）
POLYMARKET_PROXY_ADDRESS=0x18DdcbD977e5b7Ff751A3BAd6F274b67A311CD2d
```

### 可选的环境变量

```bash
# 如果想手动指定 API 凭证（通常不需要，会自动生成）
POLYMARKET_API_KEY=你的API密钥
POLYMARKET_API_SECRET=你的API密钥
POLYMARKET_PASSPHRASE=你的API密钥
```

---

## 步骤 4: 部署并测试（1 分钟）

1. 点击 "Deploy" 按钮
2. 等待构建完成（约 2-3 分钟）
3. 点击 "View Logs" 查看运行日志

### 成功标志

日志中应该看到：
```
[PATCH] py_clob_client 已成功修补
[PATCH] 检测到 Proxy 钱包配置
[PATCH] NautilusTrader Polymarket 适配器已成功修补
[WARN] 虚拟余额 1000 USDC.e 仅用于绕过 NautilusTrader 的检查
[OK] 成功获取市场信息
Order created
```

### 失败标志

如果看到 Cloudflare 错误：
```
Cloudflare Ray ID: ...
403 Forbidden
```

这说明 Railway 的 IP 也被封了（可能性很低）。

---

## 步骤 5: 监控和调整

### 查看日志
1. 在 Railway 项目中
2. 点击你的项目
3. 点击 "View Logs"

### 重启机器人
1. 点击 "Restart" 按钮
2. 或推送新代码到 GitHub（自动重新部署）

### 停止机器人
1. 点击 "Stop" 按钮
2. 或删除环境变量

---

## Railway vs Zeabur 对比

| 特性 | Railway | Zeabur |
|------|---------|--------|
| **价格** | $5 免费额度，后按使用付费 | 免费层有限制 |
| **Cloudflare** | ✅ 不被封 | ❌ IP 被封 |
| **配置** | ⭐⭐⭐⭐⭐ 简单 | ⭐⭐⭐ 需要配置 |
| **日志** | ⭐⭐⭐⭐⭐ 实时流式 | ⭐⭐⭐⭐ 需下载 |
| **自动部署** | ✅ Git push 自动 | ✅ Git push 自动 |
| **免费额度** | $5/月 | 受限 |
| **自定义域名** | ✅ 可配置 | ✅ 可配置 |

---

## 常见问题

### Q: Railway 会收费吗？
A: 前 $5 是免费的。对于这个机器人，大概率不会超过免费额度。

### Q: 如何停止收费？
A: 删除项目或暂停项目即可。

### Q: Railway 的 IP 也会被封吗？
A: 可能性很低。Railway 使用多个云提供商，IP 池很大。

### Q: 可以同时使用 Zeabur 和 Railway 吗？
A: 可以，但需要修改代码以支持多个实例（避免重复下单）。

### Q: 如何查看余额和交易？
A: 在 Polymarket 网站登录你的账户查看。

---

## 更新间隔调整

如果在 Railway 上仍然遇到速率限制，可以进一步增加更新间隔：

```python
# run_15m_market.py 第 506 行

# 当前（30 秒）
update_interval_ms: int = 30000

# 可选（60 秒）
update_interval_ms: int = 60000

# 保守（2 分钟）
update_interval_ms: int = 120000
```

---

## 备选方案

如果 Railway 也不行，可以尝试：

### 1. Render (https://render.com/)
- 免费层可用
- 配置类似 Railway

### 2. Fly.io (https://fly.io/)
- 全球分布
- 可选择不同地区

### 3. 自建 VPS
- AWS Lightsail ($5/月)
- DigitalOcean ($4/月)
- Vultr ($2.5/月)
- 完全控制，但需要手动配置

---

## 联系方式

如果遇到问题：
- Railway 文档：https://docs.railway.app/
- Railway Discord：https://discord.gg/railway
- Polymarket Discord：https://discord.gg/polymarket

---

## 下一步

1. ✅ 创建 railway.toml（已完成）
2. ⏳ 注册 Railway 并部署
3. ⏳ 配置环境变量
4. ⏳ 查看日志确认运行
5. ⏳ 监控交易情况

**预计时间**：5-10 分钟完成迁移
