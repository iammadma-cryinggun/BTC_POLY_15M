"""
跳过 NautilusTrader 的余额预检查

问题：
  - Polymarket API 的 balance-allowance 端点只返回 Signer 的余额（0）
  - 但实际订单处理时，API 会检查 Funder 的余额（实际余额）
  - NautilusTrader 的余额检查会阻止订单创建（NOTIONAL_EXCEEDS_FREE_BALANCE）

解决方案：
  - 修改 NautilusTrader 的余额检查逻辑
  - 如果使用 funder 模式（Proxy 钱包），则跳过余额验证或使用最小余额
  - 让 Polymarket API 自己处理余额验证（它会检查 Funder 余额）
"""

_PATCHED = False

def patch_nautilus_order_validation():
    """修补 NautilusTrader 以跳过余额预检查"""
    global _PATCHED

    if _PATCHED:
        return  # 已经修补过了

    try:
        import os
        from nautilus_trader.adapters.polymarket.execution import PolymarketExecutionClient
        from nautilus_trader.model.objects import Quantity
        from decimal import Decimal

        # 检查是否使用 funder（Proxy 钱包）
        use_funder_mode = os.getenv('POLYMARKET_PROXY_ADDRESS') is not None

        if not use_funder_mode:
            print("[INFO] 未检测到 Proxy 地址配置，不应用跳过余额检查的补丁")
            return

        print("[PATCH] 检测到 Proxy 钱包配置")
        print("[INFO] 将应用跳过余额预检查的补丁")

        # 保存原始方法
        original_update_account_state = PolymarketExecutionClient._update_account_state

        async def _update_account_state_patched(self) -> None:
            """修补后的版本：使用虚拟余额（1000 USDC.e）以绕过 NautilusTrader 的检查

            重要：实际的余额验证由 Polymarket API 执行（它会检查 Funder 的余额）
            """
            from nautilus_trader.adapters.polymarket.encoding import usdce_from_units
            from nautilus_trader.model.objects import AccountBalance, Money
            from nautilus_trader.adapters.polymarket.common.enums import USDC_POS
            from py_clob_client.clob_types import BalanceAllowanceParams, AssetType
            import asyncio

            self._log.info("Checking account balance")

            params = BalanceAllowanceParams(
                asset_type=AssetType.COLLATERAL,
                signature_type=self._config.signature_type,
            )
            response: dict = await asyncio.to_thread(
                self._http_client.get_balance_allowance,
                params,
            )

            api_balance = int(response.get("balance", 0))

            # ⭐ 关键修复：使用虚拟余额（1000 USDC.e）以绕过 NautilusTrader 的余额检查
            # 实际的余额验证由 Polymarket API 执行
            virtual_balance = 1000.0  # 足够大的值，确保订单不会被 NautilusTrader 拒绝
            total = Money(virtual_balance, USDC_POS)

            self._log.warning(
                f"[PATCH] Proxy 钱包模式：使用虚拟余额 {virtual_balance} USDC.e "
                f"(API 返回 Signer 余额: {api_balance}, 实际 Funder 余额由 Polymarket API 验证)"
            )

            account_balance = AccountBalance(
                total=total,
                locked=Money.from_raw(0, USDC_POS),
                free=total,
            )

            self.generate_account_state(
                balances=[account_balance],
                margins=[],  # N/A
                reported=True,
                ts_event=self._clock.timestamp_ns(),
            )

        # 替换方法
        PolymarketExecutionClient._update_account_state = _update_account_state_patched

        print("[PATCH] NautilusTrader Polymarket 适配器已成功修补")
        print("[INFO] 余额预检查已禁用（Polymarket API 将验证 Funder 余额）")
        print("[WARN] 虚拟余额 1000 USDC.e 仅用于绕过 NautilusTrader 的检查")

        _PATCHED = True

    except ImportError as e:
        # NautilusTrader 还未导入，延迟修补
        print(f"[INFO] NautilusTrader 未加载，将在导入后应用补丁")
    except Exception as e:
        print(f"[ERROR] NautilusTrader 补丁失败: {e}")
        import traceback
        traceback.print_exc()


# 尝试立即修补（如果 NautilusTrader 已加载）
patch_nautilus_order_validation()

