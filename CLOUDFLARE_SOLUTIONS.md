# Cloudflare 封禁问题解决方案

## 问题描述

Zeabur 部署的机器人被 Cloudflare 阻止：
- Cloudflare Ray ID: `9c63307a486ecfe9`, `9c63360d5ae41f2f`
- Zeabur IP: `54.193.237.177`
- 原因：IP 地址已被 Cloudflare 标记为机器人

## 解决方案（按推荐顺序）

### 方案 1: 降低更新频率 ⭐（已应用）

**当前配置**：30 秒更新一次

**优点**：
- 简单快速，无需额外配置
- 减少服务器负载和 API 调用
- 对 15 分钟市场做市影响很小

**缺点**：
- 如果 IP 已被永久标记，可能仍然无效
- 响应速度较慢

**如何调整**：
```python
# run_15m_market.py 第 506 行
update_interval_ms: int = 30000   # 30 秒

# 如果仍被封，可以尝试：
update_interval_ms: int = 60000   # 60 秒
update_interval_ms: int = 120000  # 2 分钟
```

---

### 方案 2: 使用代理服务（推荐）⭐⭐⭐

在 Zeabur 中配置 HTTP 代理，请求通过代理发出，使用不同的 IP。

**步骤**：

1. **获取代理服务**（任选其一）：
   - **免费**：https://www.proxy-list.download/ (不稳定)
   - **付费**：
     - Bright Data (原 Luminati)
     - Oxylabs
     - Smartproxy
     - 价格：约 $500/月

2. **在 Zeabur 中配置环境变量**：
   ```
   HTTP_PROXY=http://proxy-server:port
   HTTPS_PROXY=http://proxy-server:port
   ```

3. **修改代码以支持代理**：

   在 `run_15m_market.py` 开头添加：
   ```python
   import os
   # 从环境变量读取代理配置
   http_proxy = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
   if http_proxy:
       import requests
       # 配置 py_clob_client 使用代理（如果库支持）
       print(f"[INFO] Using proxy: {http_proxy}")
   ```

**优点**：
- 完全绕过 Cloudflare 的 IP 封禁
- 可以选择不同地区的代理
- 稳定可靠

**缺点**：
- 需要付费（好用的代理不便宜）
- 需要额外配置

---

### 方案 3: 更换部署平台

使用不同的云平台，可能使用不同的 IP 段。

**推荐平台**：

1. **Railway** (https://railway.app/)
   - 免费额度：$5/月
   - 简单易用
   - 可能有不同的 IP 段

2. **Render** (https://render.com/)
   - 免费额度有限
   - 稳定性好

3. **Fly.io** (https://fly.io/)
   - 全球分布
   - 可选择不同地区

4. **自建 VPS**
   - AWS Lightsail
   - DigitalOcean
   - Vultr
   - 完全控制，价格便宜（$5/月）

**迁移步骤**：
1. 注册平台账号
2. 连接 GitHub 仓库
3. 配置环境变量
4. 部署

---

### 方案 4: 联系 Polymarket 申请白名单

如果这是一个重要的交易机器人，可以联系 Polymarket 支持团队。

**步骤**：
1. 发送邮件到 Polymarket 支持
2. 说明情况：
   - 你是算法交易者
   - 使用 API 进行做市
   - 遵守 Polymarket 的交易规则
   - 请求将你的 IP 加入白名单

**需要提供**：
- 你的 Polymarket 账户地址
- IP 地址（54.193.237.177）
- 机器人描述
- 预期交易频率

**优点**：
- 官方支持
- 长期解决方案

**缺点**：
- 可能需要时间
- 不一定成功

---

### 方案 5: 智能更新策略

只在必要时更新订单，而不是定期更新。

**实现思路**：
```python
# 只在以下情况更新订单：
# 1. 价格变化超过阈值（如 1%）
# 2. 订单被执行后
# 3. 库存风险变化时
# 4. 接近到期时

# 而不是：每 30 秒无条件更新
```

**优点**：
- 大幅减少 API 调用次数
- 更智能的交易策略
- 可能提高利润率

**缺点**：
- 需要修改策略代码
- 实现复杂

---

## 当前状态

**已应用**：
- ✅ 虚拟余额补丁（绕过 NautilusTrader 余额检查）
- ✅ 更新间隔：1 秒 → 30 秒

**待尝试**：
- ⏳ 等待 Zeabur 部署并测试
- ⏳ 如果仍被阻止，尝试方案 2（代理）或方案 3（更换平台）

---

## 推荐路径

### 短期（现在）：
1. ✅ 已应用：30 秒更新间隔
2. ⏳ 等待部署测试
3. ❓ 如果仍失败 → 增加到 60 秒或 2 分钟

### 中期（1-2 天）：
1. 购买代理服务（方案 2）
2. 或更换到 Railway/Render（方案 3）

### 长期（1 周）：
1. 联系 Polymarket 申请白名单（方案 4）
2. 实现智能更新策略（方案 5）

---

## 快速测试命令

部署后，在 Zeabur 日志中查找：
```
# 成功运行
[PATCH] Proxy 钱包模式：使用虚拟余额 1000.0 USDC.e
Order created
Order accepted

# Cloudflare 错误
Cloudflare Ray ID
403 Forbidden
Unable to connect
```

---

## 最后的说明

**Cloudflare 封禁是正常的**：
- 大多数 API 都有速率限制
- 目的是防止滥用和保护服务器
- 算法交易者需要优雅地处理这个问题

**最佳实践**：
- 使用合理的更新频率（30-60 秒）
- 实现智能更新策略
- 考虑使用代理或多个 IP
- 与平台保持良好沟通
