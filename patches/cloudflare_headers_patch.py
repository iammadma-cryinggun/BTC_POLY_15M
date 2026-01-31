"""
Cloudflare Anti-Bot 补丁 - 为 py_clob_client 添加浏览器伪装头和代理支持

问题：
- Polymarket 使用 Cloudflare 防护
- py_clob_client 默认的 User-Agent 是 "python-requests/2.x"
- Cloudflare 检测到后返回 403 Forbidden
- 本地网络需要代理才能访问

解决方案：
- 猴子补丁 (Monkey Patch) ClobClient.__init__
- 自动注入浏览器伪装头（Chrome 120）
- 自动从环境变量读取代理配置
"""

import os


def patch_cloudflare_headers():
    """为所有 ClobClient 实例添加浏览器伪装头和代理支持"""

    try:
        from py_clob_client import client as client_module

        # 保存原始的 __init__ 方法
        original_init = client_module.ClobClient.__init__

        def new_init(self, host, key=None, **kwargs):
            """修补后的 __init__：在初始化后自动注入浏览器伪装头和代理"""

            # 先调用原始的 __init__
            original_init(self, host, key=key, **kwargs)

            # 注入浏览器伪装头（模拟 Chrome 120 on Windows）
            fake_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Referer": "https://polymarket.com/",
                "Origin": "https://polymarket.com",
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            }

            # 更新 session.headers
            if hasattr(self, '_session') and hasattr(self._session, 'headers'):
                self._session.headers.update(fake_headers)

            # ========== 关键：设置代理 ==========
            http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
            https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')

            if http_proxy and hasattr(self, '_session'):
                # 设置代理到 session
                self._session.proxies = {
                    'http': http_proxy,
                    'https': https_proxy or http_proxy,
                }
                print(f"[PATCH] 已为 ClobClient 设置代理: {http_proxy}")

            print("[PATCH] 已为 ClobClient 注入浏览器伪装头 (Anti-Cloudflare)")

        # 替换 ClobClient 的 __init__ 方法
        client_module.ClobClient.__init__ = new_init

        print("[PATCH] Cloudflare headers 补丁已安装")
        print("[INFO] 所有新的 ClobClient 实例将自动使用浏览器伪装")

    except Exception as e:
        print(f"[ERROR] Cloudflare headers 补丁失败: {e}")
        import traceback
        traceback.print_exc()


# 在模块导入时自动执行修补
patch_cloudflare_headers()
