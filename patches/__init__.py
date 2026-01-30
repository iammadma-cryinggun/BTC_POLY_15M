"""
py_clob_client 补丁模块

在项目启动时自动应用修复补丁
"""

# 导入补丁模块，这会自动执行 patch_py_clob_client() 函数
from patches import py_clob_client_patch  # noqa: F401

# 导入 NautilusTrader 余额补丁
from patches import nautilus_balance_patch  # noqa: F401
