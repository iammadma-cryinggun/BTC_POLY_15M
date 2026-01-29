# Zeabur 部署指南

## 📦 部署步骤

### 1. 准备工作

确保你已经：
- ✅ 推送代码到 GitHub
- ✅ 注册 Zeabur 账号
- ✅ 准备好 Polymarket 私钥

---

## 🔑 Zeabur 环境变量配置

### 必需的环境变量

在 Zeabur 项目设置中添加以下环境变量：

#### 1. POLYMARKET_PK（必需）

**说明**: Polymarket Magic Wallet 私钥

**获取方法**:
1. 登录 Polymarket 网页版
2. 进入 Settings → Wallets → Magic Wallet
3. 点击 "Reveal Private Key"
4. 复制私钥（格式：0x开头的十六进制字符串）

**示例**:
```
POLYMARKET_PK=0xed298792ddcc1e6348a934214fa563324800bfa72ac58fc066ea4ba8a17b1feb
```

**注意**:
- ⚠️ 这是**私钥**，不要泄露！
- ✅ Zeabur 会加密存储
- ✅ 只有你的服务可以访问

---

### 可选的环境变量（不需要配置）

以下环境变量会自动生成，**不需要手动配置**：

```
POLYMARKET_API_KEY          # 自动生成
POLYMARKET_API_SECRET       # 自动生成
POLYMARKET_PASSPHRASE       # 自动生成
```

**原因**: 策略使用 `signature_type=2`（Magic Wallet），会自动调用 `create_or_derive_api_creds()` 生成 API 凭证。

---

## 🚀 Zeabur 部署流程

### 方法 A: 通过 Zeabur UI（推荐）

#### 步骤 1: 创建新项目

1. 登录 [Zeabur](https://zeabur.com)
2. 点击 "Create New Project"
3. 选择 "Deploy from GitHub"

#### 步骤 2: 连接 GitHub 仓库

1. 搜索仓库：`iammadma-cryinggun/poly_btc_update`
2. 选择 `main` 分支
3. 点击 "Import"

#### 步骤 3: 配置服务

1. **服务类型**: Docker Container
2. **Dockerfile**: 自动检测
3. **启动命令**: 自动检测

#### 步骤 4: 配置环境变量

1. 进入服务设置 → Environment Variables
2. 添加环境变量：

```
Name: POLYMARKET_PK
Value: 0x你的私钥
```

3. 点击 "Save"

#### 步骤 5: 部署

1. 点击 "Deploy"
2. 等待构建完成（约 2-5 分钟）
3. 查看日志确认启动成功

---

### 方法 B: 通过 Zeabur CLI

#### 安装 Zeabur CLI

```bash
# 使用 npm 安装
npm install -g zeabur

# 或使用 homebrew（macOS）
brew install zeabur/tap/zeabur
```

#### 登录

```bash
zeabur login
```

#### 部署

```bash
# 进入项目目录
cd D:\翻倍项目\polymarket_v2

# 部署
zeabur deploy
```

#### 设置环境变量

```bash
# 添加私钥
zeabur variables set POLYMARKET_PK="0x你的私钥"

# 验证
zeabur variables list
```

---

## 🐳 Dockerfile 配置

项目已经包含了 `Dockerfile`，位于项目根目录：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令（15分钟市场策略）
CMD ["python", "run_15m_market.py"]
```

**注意**: 默认启动 15 分钟市场策略。如果需要运行日内市场策略，修改最后一行为：
```dockerfile
CMD ["python", "run_simple_v2.py"]
```

---

## 📋 完整环境变量清单

### 必需配置（1个）

| 变量名 | 说明 | 示例值 | 必需 |
|--------|------|--------|------|
| POLYMARKET_PK | Magic Wallet 私钥 | 0xed29879...7b1feb | ✅ 是 |

### 自动生成（3个）

| 变量名 | 说明 | 来源 |
|--------|------|------|
| POLYMARKET_API_KEY | API 密钥 | 自动生成 |
| POLYMARKET_API_SECRET | API 密钥 | 自动生成 |
| POLYMARKET_PASSPHRASE | API 密钥短语 | 自动生成 |

**不需要手动配置这些！** ✅

---

## 🔍 验证部署

### 1. 检查服务状态

在 Zeabur 控制台：
- 确认服务状态：Running ✅
- 查看日志：无错误

### 2. 查看日志

应该看到类似的输出：

```
================================================================================
预测市场做市策略（基于学术论文优化）
================================================================================
市场: btc-updown-15m-1769689800
Question: Bitcoin will be up or down on...

[INFO] 论文优化:
  - Avellaneda-Stoikov 模型
  - 时间衰减价差: s = γσ²T
  - 库存风险管理
  - 价格收敛保护

[OK] 私钥已加载: 0xed29879...7b1feb
[OK] 成功获取市场信息
[OK] Instrument ID: POLYMARKET-0x...

做市参数:
  中间价: 0.5234
  剩余时间: 14.8 分钟
  价差: 2.45% (时间衰减调整)
  ...
================================================================================
```

### 3. 测试交易

在 Polymarket 网页版：
- 查看你的订单
- 确认订单已提交
- 观察成交情况

---

## 🛠️ 常见问题

### Q1: 部署失败，提示 "POLYMARKET_PK not found"

**解决**:
1. 检查环境变量是否正确配置
2. 确保私钥格式正确（0x开头）
3. 重新部署服务

### Q2: 服务启动但无法连接 Polymarket

**解决**:
1. Zeabur 网络通常没问题
2. 检查私钥是否正确
3. 查看日志获取详细错误

### Q3: 如何切换到日内市场策略？

**方法 A: 修改 Dockerfile**
```dockerfile
# 将最后一行改为：
CMD ["python", "run_simple_v2.py"]
```

**方法 B: 修改环境变量**
在 Zeabur 中添加：
```
START_STRATEGY=daily
```

然后修改启动脚本检测此变量。

### Q4: 如何更新私钥？

**解决**:
1. Zeabur 控制台 → 服务设置
2. Environment Variables → 编辑 POLYMARKET_PK
3. 保存并重启服务

### Q5: 内存或CPU限制？

**建议配置**:
- CPU: 0.5-1 核
- Memory: 512MB - 1GB
- 成本: 约 $5-10/月

---

## 📊 部署后监控

### 关键指标

1. **服务健康**:
   - 状态：Running
   - 重启次数：0-1次/天

2. **交易指标**（从日志中）:
   - 订单提交频率
   - 成交率
   - 盈亏情况

3. **资源使用**:
   - CPU: < 50%
   - Memory: < 80%

### 设置告警（可选）

在 Zeabur 中设置：
- 服务停止告警
- CPU > 80% 告警
- Memory > 90% 告警

---

## 🎯 部署检查清单

### 部署前

- [ ] 代码已推送到 GitHub
- [ ] 已获取 Polymarket 私钥
- [ ] 已注册 Zeabur 账号
- [ ] 已阅读部署指南

### 部署中

- [ ] 成功连接 GitHub 仓库
- [ ] 正确配置 POLYMARKET_PK
- [ ] 选择正确的服务类型（Docker）
- [ ] 确认启动命令

### 部署后

- [ ] 服务状态：Running
- [ ] 日志无错误
- [ ] 能正常连接 Polymarket
- [ ] 订单正常提交
- [ ] 监控指标正常

---

## 📝 快速命令参考

### 本地测试

```bash
# 测试15分钟市场
python run_15m_market.py

# 测试日内市场
python run_simple_v2.py
```

### Zeabur CLI

```bash
# 登录
zeabur login

# 部署
zeabur deploy

# 查看日志
zeabur logs

# 设置环境变量
zeabur variables set POLYMARKET_PK="0x..."

# 列出环境变量
zeabur variables list

# 重启服务
zeabur restart
```

---

## 🎉 完成！

现在你的策略已经在 Zeabur 上运行：
- ✅ 24/7 自动运行
- ✅ 网络稳定
- ✅ 自动重启
- ✅ 日志记录

**祝交易顺利！** 🚀
