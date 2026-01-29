"""
盲扫诊断脚本 - 查看 API 返回的原始数据

不做任何关键词过滤，直接打印前 10 个市场的所有信息
"""
import requests
from datetime import datetime, timezone
import dateutil.parser

def raw_scan():
    # 1. 检查服务器时间 (非常重要，排除容器时间错误)
    print(f"[TIME] Container time (UTC): {datetime.now(timezone.utc)}")
    print(f"[TIME] Current timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"=" * 80)

    url = "https://gamma-api.polymarket.com/events"

    # 2. 去掉 tags="Bitcoin"，去掉所有复杂的过滤
    # 只查：未结束的、按结束时间排序的
    params = {
        "closed": "false",
        "limit": 15,            # 查前15个
        "order": "endDate:asc"  # 查最近过期的
    }

    print("[INFO] Requesting raw data from API (no filters)...")
    print(f"[INFO] URL: {url}")
    print(f"[INFO] Params: {params}")
    print(f"=" * 80)

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        events = response.json()

        if not events:
            print("[ERROR] API returned empty list! (Polymarket might be under maintenance)")
            return

        print(f"\n[OK] API returned {len(events)} raw events. Analyzing first 10...\n")
        print(f"=" * 80)

        for i, event in enumerate(events[:10]):
            title = event.get('title', 'N/A')
            end_date_str = event.get('endDate')
            end_date = dateutil.parser.isoparse(end_date_str) if end_date_str else "N/A"

            # 计算剩余时间
            if end_date != "N/A":
                now = datetime.now(timezone.utc)
                diff = (end_date - now).total_seconds() / 60
                time_str = f"{diff:.1f} min"
                status = "FUTURE" if diff > 0 else "EXPIRED"
            else:
                time_str = "Unknown"
                status = "Unknown"

            print(f"[{i+1}] Title: {title}")
            print(f"     End Date (UTC): {end_date_str}")
            print(f"     Time Remaining: {time_str}")
            print(f"     Status: {status}")
            print(f"     Tags: {event.get('tags')}")
            print(f"     Slug: {event.get('slug', 'N/A')}")

            # 打印 Market 信息
            markets = event.get('markets', [])
            if markets:
                market = markets[0]
                print(f"     Market ID: {market.get('id', 'N/A')}")
                print(f"     Condition ID: {market.get('conditionId', 'N/A')}")

                # 打印 outcomes
                outcomes = market.get('outcomes', [])
                if outcomes:
                    print(f"     Outcomes: {outcomes}")

                # 打印 token IDs
                clob_ids = market.get('clobTokenIds', '[]')
                if clob_ids and clob_ids != '[]':
                    print(f"     Token IDs: {clob_ids[:100]}...")
            else:
                print(f"     [WARN] No markets found in this event")

            print("-" * 80)

        # 额外分析：统计标题中包含 "Bitcoin" 的市场
        print(f"\n" + "=" * 80)
        print(f"[ANALYSIS] Searching for 'Bitcoin' in all returned events...")
        print(f"=" * 80)

        btc_events = [e for e in events if 'bitcoin' in e.get('title', '').lower()]
        print(f"[INFO] Found {len(btc_events)} events with 'Bitcoin' in title:")

        for i, event in enumerate(btc_events[:5]):
            title = event.get('title', 'N/A')
            end_date_str = event.get('endDate')
            end_date = dateutil.parser.isoparse(end_date_str) if end_date_str else "N/A"

            if end_date != "N/A":
                now = datetime.now(timezone.utc)
                diff = (end_date - now).total_seconds() / 60
                time_str = f"{diff:.1f} min"
            else:
                time_str = "Unknown"

            print(f"  {i+1}. {title}")
            print(f"     Ends: {end_date_str} (Remaining: {time_str})")

        # 统计包含 ">" 的市场
        print(f"\n[ANALYSIS] Searching for '>' in all returned events...")
        greater_events = [e for e in events if '>' in e.get('title', '')]
        print(f"[INFO] Found {len(greater_events)} events with '>' in title:")

        for i, event in enumerate(greater_events[:5]):
            title = event.get('title', 'N/A')
            end_date_str = event.get('endDate')
            end_date = dateutil.parser.isoparse(end_date_str) if end_date_str else "N/A"

            if end_date != "N/A":
                now = datetime.now(timezone.utc)
                diff = (end_date - now).total_seconds() / 60
                time_str = f"{diff:.1f} min"
            else:
                time_str = "Unknown"

            print(f"  {i+1}. {title}")
            print(f"     Ends: {end_date_str} (Remaining: {time_str})")

    except Exception as e:
        print(f"[FATAL] Request failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    raw_scan()
