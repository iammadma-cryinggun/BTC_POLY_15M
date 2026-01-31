"""
httpx 代理支持补丁

问题：
- py_clob_client 使用 httpx 进行网络请求
- httpx 默认不读取 HTTP_PROXY 环境变量
- 需要显式配置代理

解决方案：
- 猴子补丁 httpx.Client，自动从环境变量读取代理
"""

import os


def patch_httpx_proxy():
    """为 httpx.Client 添加代理支持"""

    try:
        import httpx

        # 保存原始的 __init__ 方法
        original_init = httpx.Client.__init__

        def new_init(self, *args, **kwargs):
            """修补后的 __init__：自动添加代理配置"""

            # 如果没有显式设置代理，从环境变量读取
            if 'proxy' not in kwargs and 'proxies' not in kwargs:
                http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
                https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')

                if http_proxy:
                    # httpx 使用 proxy 参数（单字符串）或 proxies 参数（字典）
                    kwargs['proxies'] = {
                        'http://': http_proxy,
                        'https://': https_proxy or http_proxy,
                    }
                    print(f"[PATCH] httpx.Client 已配置代理: {http_proxy}")

            # 调用原始的 __init__
            original_init(self, *args, **kwargs)

        # 替换 httpx.Client 的 __init__ 方法
        httpx.Client.__init__ = new_init

        print("[PATCH] httpx 代理补丁已安装")
        print("[INFO] 所有新的 httpx.Client 实例将自动使用环境变量中的代理")

    except Exception as e:
        print(f"[ERROR] httpx 代理补丁失败: {e}")
        import traceback
        traceback.print_exc()


# 在模块导入时自动执行修补
patch_httpx_proxy()
