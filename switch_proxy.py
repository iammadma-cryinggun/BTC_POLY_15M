"""
快速切换代理配置脚本

使用方法：
  python switch_proxy.py clash   # 切换到 Clash (端口 7890)
  python switch_proxy.py veee    # 切换到 Veee (端口 15236)
"""
import sys
from pathlib import Path


def switch_proxy(proxy_type):
    """切换代理配置"""

    env_file = Path(__file__).parent / ".env"

    # 读取 .env 文件
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 新的配置
    new_lines = []
    if proxy_type.lower() == 'clash':
        proxy_config = [
            "# 方案 1: Clash (推荐) - 完全支持 WebSocket\n",
            "HTTP_PROXY=http://127.0.0.1:7890\n",
            "HTTPS_PROXY=http://127.0.0.1:7890\n",
            "# 方案 2: Veee (不支持 WebSocket)\n",
            "# HTTP_PROXY=http://127.0.0.1:15236\n",
            "# HTTPS_PROXY=http://127.0.0.1:15236\n",
        ]
    elif proxy_type.lower() == 'veee':
        proxy_config = [
            "# 方案 1: Clash (推荐) - 完全支持 WebSocket\n",
            "# HTTP_PROXY=http://127.0.0.1:7890\n",
            "# HTTPS_PROXY=http://127.0.0.1:7890\n",
            "# 方案 2: Veee (不支持 WebSocket)\n",
            "HTTP_PROXY=http://127.0.0.1:15236\n",
            "HTTPS_PROXY=http://127.0.0.1:15236\n",
        ]
    else:
        print(f"错误: 未知的代理类型 '{proxy_type}'")
        print("使用方法: python switch_proxy.py [clash|veee]")
        return False

    # 替换代理配置部分
    in_proxy_section = False
    for line in lines:
        # 检测是否在代理配置部分
        if '本地代理' in line or '关键配置：本地代理' in line:
            in_proxy_section = True
            new_lines.append(line)
            new_lines.extend(proxy_config)
            continue

        # 跳过旧的代理配置行
        if in_proxy_section:
            if line.startswith('HTTP_PROXY=') or line.startswith('HTTPS_PROXY='):
                continue
            elif line.strip().startswith('#') and ('方案' in line or 'Clash' in line or 'Veee' in line):
                continue
            elif line.strip() == '':
                # 遇到空行，代理配置部分结束
                in_proxy_section = False
                new_lines.append(line)
            else:
                continue
        else:
            new_lines.append(line)

    # 写回文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"\n[SUCCESS] 代理配置已切换到: {proxy_type.upper()}")
    print(f"\n当前配置:")
    print(f"  HTTP_PROXY=http://127.0.0.1:{'7890' if proxy_type.lower() == 'clash' else '15236'}")
    print(f"  HTTPS_PROXY=http://127.0.0.1:{'7890' if proxy_type.lower() == 'clash' else '15236'}")
    print(f"\n现在可以运行: python start_bot.py")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("=" * 60)
        print("代理配置快速切换工具")
        print("=" * 60)
        print("\n使用方法:")
        print("  python switch_proxy.py clash   # 切换到 Clash")
        print("  python switch_proxy.py veee    # 切换到 Veee")
        print("\n说明:")
        print("  - Clash: 端口 7890, 支持 WebSocket (推荐)")
        print("  - Veee:  端口 15236, 不支持 WebSocket")
        sys.exit(1)

    switch_proxy(sys.argv[1])
