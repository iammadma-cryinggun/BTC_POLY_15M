# 🎯 接下来的步骤

## 📋 当前状态

✅ **已完成：**
- 本地代理配置支持（.env 文件）
- httpx 代理补丁（HTTP 请求）
- WebSocket 代理补丁（已准备就绪）
- Clash 配置文件和指南
- 快速切换代理脚本

❌ **问题：**
- Veee 不支持 WebSocket 转发
- 程序无法连接 Polymarket 实时数据流

---

## 🔧 解决方案：安装 Clash

### 方式 1：手动安装（推荐）

1. **下载 Clash**
   - 打开浏览器
   - 访问：https://github.com/clash-download/clash-for-windows/releases
   - 下载 `Clash.for.Windows.Setup.x.x.x.exe`

2. **安装并配置**
   - 详细步骤见：`CLASH_SETUP_GUIDE.md`

3. **切换代理配置**
   ```bash
   python switch_proxy.py clash
   ```

4. **启动程序**
   ```bash
   python start_bot.py
   ```

### 方式 2：快速切换（如果已安装 Clash）

```bash
# 1. 切换到 Clash 代理
python switch_proxy.py clash

# 2. 确保 Clash 正在运行
# 3. 启动交易机器人
python start_bot.py
```

---

## 📁 重要文件

| 文件 | 说明 |
|------|------|
| `.env` | 代理配置（已包含 Clash 7890 和 Veee 15236） |
| `CLASH_SETUP_GUIDE.md` | Clash 详细安装和配置指南 |
| `switch_proxy.py` | 快速切换代理工具 |
| `start_bot.py` | 启动脚本 |
| `diagnose_websocket.py` | WebSocket 连接诊断工具 |

---

## 🧪 测试步骤

安装 Clash 后，按顺序测试：

### 1. 测试 HTTP 代理
```bash
python test_proxy_connection.py
```

**预期输出：**
```
[测试 2] httpx 显式代理请求...
  状态码: 200
  [SUCCESS]
```

### 2. 测试 WebSocket 连接
```bash
python diagnose_websocket.py
```

**预期输出：**
```
[测试 2] 使用 HTTP 代理 (127.0.0.1:7890)
  [SUCCESS] 通过 HTTP 代理连接成功！
```

### 3. 启动交易机器人
```bash
python start_bot.py
```

**成功标志：**
- ✅ 不再出现 `WebSocketClientError` 或 `os error 10060`
- ✅ 程序显示市场信息
- ✅ 开始执行做市策略

---

## ❓ 常见问题

### Q: GitHub 下载太慢怎么办？
**A:** 使用国内镜像：
https://ghproxy.com/https://github.com/clash-download/clash-for-windows/releases/download/v0.20.39/Clash.for.Windows.Setup.0.20.39.exe

### Q: 一定要用 Clash 吗？可以用其他软件吗？
**A:** 可以！任何支持 WebSocket 的代理都可以：
- Clash（推荐）
- V2Ray / V2RayN
- ShadowsocksR（需要确认支持 WebSocket）
- Clash Verge（Clash 的简化版）

### Q: Clash 和 Veee 可以同时运行吗？
**A:** 不建议：
- 可能端口冲突
- 建议关闭 Veee，只用 Clash

### Q: 安装 Clash 后还是报错？
**A:** 检查：
1. Clash 是否正在运行？
2. 是否选择了可用的代理节点？
3. `.env` 文件中的端口是否改为 7890？
4. 运行 `python switch_proxy.py clash` 确认配置

---

## 🚀 一键启动脚本（安装 Clash 后）

安装 Clash 后，可以直接使用：

```bash
# 切换到 Clash 并启动
python switch_proxy.py clash && python start_bot.py
```

---

## 📞 需要帮助？

如果遇到问题，请提供：
1. 具体的错误信息
2. 运行的命令
3. `diagnose_websocket.py` 的输出

我会帮您解决！

---

## ✨ 成功后的效果

程序正常运行后，您将看到：

```
================================================================================
预测市场做市策略（基于学术论文优化）
================================================================================
市场: btc-updown-15m-xxxxxxxx
Question: Bitcoin Up or Down - January 31, 1:15AM-1:30AM ET...

[INFO] 核心优化:
  [OK] 时间衰减: 价差随剩余时间动态调整
  [OK] 库存感知: 持仓越多，倾斜越大
  [OK] 价格收敛: 最后5分钟自动停止
  [OK] 风险管理: Avellaneda-Stoikov 公式

[INFO] 程序正在运行，按 Ctrl+C 停止
```

祝交易顺利！📈
