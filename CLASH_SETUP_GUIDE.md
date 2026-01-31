# Clash for Windows 安装和配置指南

## 问题：Veee 不支持 WebSocket 转发

由于 Veee 代理无法转发 WebSocket 连接，导致程序无法连接到 Polymarket 的实时数据流。

**解决方案：使用 Clash for Windows**（完全支持 WebSocket）

---

## 第一步：下载 Clash

### 方法 1：官方下载（推荐）

1. **打开浏览器，访问：**
   https://github.com/clash-download/clash-for-windows/releases

2. **下载最新版本**
   - 找到 `Clash.for.Windows.Setup.x.x.x.exe`
   - 点击下载（约 80-100 MB）

3. **如果 GitHub 下载太慢，使用国内镜像：**
   - https://ghproxy.com/https://github.com/clash-download/clash-for-windows/releases/download/v0.20.39/Clash.for.Windows.Setup.0.20.39.exe

### 方法 2：使用其他下载工具

如果您有迅雷、IDM 等下载工具，可以复制下载链接使用。

---

## 第二步：安装 Clash

1. **运行安装程序**
   - 双击 `Clash.for.Windows.Setup.x.x.x.exe`
   - 选择安装路径（建议默认）
   - 点击 "Install"

2. **等待安装完成**
   - 安装过程约 1-2 分钟
   - 完成后启动 Clash

---

## 第三步：配置 Clash

### 3.1 导入代理订阅

1. **打开 Clash**
   - 第一次运行会显示欢迎界面

2. **导入订阅**
   - 点击左侧 "Profiles" (配置)
   - 找到 "New" 或 "导入" 按钮
   - 粘贴您的代理订阅链接（和 Veee 使用的相同）
   - 点击 "下载" 或 "Import"

3. **选择配置**
   - 导入后，在配置列表中选择刚导入的配置
   - 点击 "Select" 或 "选择"

### 3.2 启用系统代理

1. **打开设置**
   - 点击左侧 "Settings" (设置)
   - 找到 "System Proxy" (系统代理)

2. **启用系统代理**
   - 将 "System Proxy" 开关打开
   - 端口会自动设置为 7890（HTTP）和 7891（SOCKS5）

3. **允许局域网连接（可选）**
   - 找到 "Allow LAN" (允许局域网)
   - 启用它（如果需要）

### 3.3 选择代理节点

1. **打开 Proxies 页面**
   - 点击左侧 "Proxies" (代理)

2. **选择节点**
   - 在 "Global" (全局) 或 "Rule" (规则) 模式下
   - 选择一个延迟低的节点
   - 绿色表示延迟低，红色表示不可用

---

## 第四步：修改项目配置

1. **打开 `.env` 文件**
   - 位置：`D:\翻倍项目\polymarket_v2\.env`

2. **修改代理设置**
   ```bash
   # 注释掉 Veee 的配置
   # HTTP_PROXY=http://127.0.0.1:15236
   # HTTPS_PROXY=http://127.0.0.1:15236

   # 启用 Clash 的配置
   HTTP_PROXY=http://127.0.0.1:7890
   HTTPS_PROXY=http://127.0.0.1:7890
   ```

3. **保存文件**

---

## 第五步：测试连接

### 5.1 测试 HTTP 代理

在命令行运行：
```bash
python test_proxy_connection.py
```

应该看到：
```
[测试 2] httpx 显式代理请求...
  状态码: 200
  [SUCCESS]
```

### 5.2 测试 WebSocket 连接

运行 WebSocket 诊断：
```bash
python diagnose_websocket.py
```

应该看到：
```
[测试 2] 使用 HTTP 代理 (127.0.0.1:7890)
  [SUCCESS] 通过 HTTP 代理连接成功！
```

---

## 第六步：启动交易机器人

```bash
python start_bot.py
```

**成功标志：**
- ✅ 不再出现 WebSocket 连接超时错误
- ✅ 程序正常运行，显示市场信息
- ✅ 开始执行交易策略

---

## 常见问题

### Q1: Clash 下载失败？
**A:** 尝试：
- 使用国内镜像：https://ghproxy.com/
- 使用其他下载工具（迅雷、IDM）
- 从第三方网站下载（如蓝奏云）

### Q2: Clash 启动后无法联网？
**A:** 检查：
- 订阅是否正确导入
- 是否选择了可用的代理节点
- 系统代理是否开启

### Q3: 仍然出现 WebSocket 错误？
**A:** 检查：
- `.env` 文件中的端口是否改为 7890
- Clash 是否正在运行
- 尝试重启 Clash 和程序

### Q4: 能同时使用 Veee 和 Clash 吗？
**A:** 可以，但建议：
- 关闭 Veee（避免端口冲突）
- 或修改 Veee 的端口
- 只启用一个代理软件

---

## 验证 Clash 是否正常工作

打开浏览器访问：
- https://www.google.com (应该能打开)
- https://httpbin.org/ip (应该显示代理IP)

---

## 下一步

安装配置完成后：
1. 运行 `python test_proxy_connection.py` 验证代理
2. 运行 `python diagnose_websocket.py` 验证 WebSocket
3. 运行 `python start_bot.py` 启动交易机器人

如有问题，请将错误信息发给我！
