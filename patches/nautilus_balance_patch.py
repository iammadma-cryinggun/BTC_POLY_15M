"""
修复 NautilusTrader Polymarket 适配器的余额查询

问题：API 返回的是 Signer 地址的余额（0），而不是 Proxy 地址的余额（17.75）
解决方案：使用环境变量 POLYMARKET_BALANCE_OVERRIDE 直接指定余额
"""

def patch_nautilus_polymarket():
    """修补 NautilusTrader Polymarket 适配器的余额查询"""

    try:
        import os
        from nautilus_trader.adapters.polymarket.execution import PolymarketExecutionClient

        # 检查是否配置了余额覆盖
        balance_override = os.getenv("POLYMARKET_BALANCE_OVERRIDE")
        if balance_override:
            try:
                override_value = float(balance_override)
                print(f"[PATCH] 将使用余额覆盖值: {override_value} USDC.e")
            except ValueError:
                print(f"[WARN] POLYMARKET_BALANCE_OVERRIDE 值无效: {balance_override}")
                balance_override = None
        else:
            print(f"[INFO] 未设置 POLYMARKET_BALANCE_OVERRIDE，将使用 API 返回值")

        # 保存原始方法
        original_update_account_state = PolymarketExecutionClient._update_account_state

        async def _update_account_state_patched(self) -> None:
            """修补后的版本：支持余额覆盖"""
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

            # ⭐ 关键修复：使用覆盖值（如果设置）
            if balance_override:
                from nautilus_trader.model.objects import Money
                # 将 USDC.e 转换为内部单位（6 decimals）
                total = Money(balance_override, USDC_POS)
                self._log.warning(f"[PATCH] 使用余额覆盖值: {balance_override} USDC.e (API 返回: {response['balance']})")
            else:
                total = usdce_from_units(int(response["balance"]))

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
        print("[INFO] _update_account_state 方法已支持余额覆盖")

    except Exception as e:
        print(f"[ERROR] NautilusTrader 补丁失败: {e}")
        import traceback
        traceback.print_exc()


# 在模块导入时自动执行修补
patch_nautilus_polymarket()
