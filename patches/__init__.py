"""
py_clob_client 补丁模块

在项目启动时自动应用修复补丁
"""

# 导入补丁模块，这会自动执行 patch_py_clob_client() 函数
from patches import py_clob_client_patch  # noqa: F401

# 导入 NautilusTrader 余额补丁
# 选择一个：
# - nautilus_balance_patch: 使用 POLYMARKET_BALANCE_OVERRIDE 环境变量（需要手动设置）
# - nautilus_skip_balance_check: 自动跳过余额检查，让 Polymarket API 验证（推荐）
from patches import nautilus_skip_balance_check  # noqa: F401
# from patches import nautilus_balance_patch  # noqa: F401
