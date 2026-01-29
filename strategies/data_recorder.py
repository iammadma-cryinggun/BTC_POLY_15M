"""
交易数据记录器 - 持久化交易数据用于分析和优化

记录内容：
1. 订单簿快照（每秒）
2. 订单提交和成交
3. 库存变化
4. 价格历史
5. 策略参数

输出格式：CSV 文件（便于分析）
"""

import csv
import os
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from typing import Any, Dict
import json


class TradeDataRecorder:
    """交易数据记录器"""

    def __init__(self, output_dir: str = "/app/data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 当前会话标识
        self.session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # 数据文件
        self.orderbook_file = self.output_dir / f"orderbook_{self.session_id}.csv"
        self.orders_file = self.output_dir / f"orders_{self.session_id}.csv"
        self.inventory_file = self.output_dir / f"inventory_{self.session_id}.csv"
        self.trades_file = self.output_dir / f"trades_{self.session_id}.csv"
        self.config_file = self.output_dir / f"config_{self.session_id}.json"

        # 初始化 CSV 文件
        self._init_csv_files()

        # 配置数据
        self.config_data = {}

    def _init_csv_files(self):
        """初始化 CSV 文件和表头"""

        # 订单簿数据
        if not self.orderbook_file.exists():
            with open(self.orderbook_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'datetime',
                    'mid_price',
                    'bid_price',
                    'ask_price',
                    'spread_pct',
                    'time_remaining_min',
                    'volatility',
                    'inventory_skew_pct',
                    'calculated_bid',
                    'calculated_ask'
                ])

        # 订单数据
        if not self.orders_file.exists():
            with open(self.orders_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'datetime',
                    'order_id',
                    'side',
                    'price',
                    'quantity',
                    'order_type',
                    'status'
                ])

        # 库存数据
        if not self.inventory_file.exists():
            with open(self.inventory_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'datetime',
                    'inventory_qty',
                    'inventory_value_usdc',
                    'free_balance',
                    'total_balance',
                    'realized_pnl',
                    'unrealized_pnl'
                ])

        # 成交数据
        if not self.trades_file.exists():
            with open(self.trades_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'datetime',
                    'order_id',
                    'side',
                    'price',
                    'quantity',
                    'commission',
                    'pnl'
                ])

    def record_orderbook(
        self,
        mid_price: Decimal,
        bid_price: Decimal,
        ask_price: Decimal,
        spread: Decimal,
        time_remaining_min: float,
        volatility: Decimal,
        skew: Decimal,
    ):
        """记录订单簿快照"""
        with open(self.orderbook_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                int(datetime.utcnow().timestamp()),
                datetime.utcnow().isoformat(),
                str(mid_price),
                str(bid_price),
                str(ask_price),
                str(spread * 100),
                f"{time_remaining_min:.2f}",
                str(volatility * 100),
                str(skew * 100),
                str(bid_price),
                str(ask_price)
            ])

    def record_order(
        self,
        order_id: str,
        side: str,
        price: Decimal,
        quantity: int,
        order_type: str = "LIMIT",
        status: str = "SUBMITTED"
    ):
        """记录订单"""
        with open(self.orders_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                int(datetime.utcnow().timestamp()),
                datetime.utcnow().isoformat(),
                order_id,
                side,
                str(price),
                quantity,
                order_type,
                status
            ])

    def record_inventory(
        self,
        inventory_qty: int,
        inventory_value: Decimal,
        free_balance: Decimal,
        total_balance: Decimal,
        realized_pnl: Decimal,
        unrealized_pnl: Decimal,
    ):
        """记录库存变化"""
        with open(self.inventory_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                int(datetime.utcnow().timestamp()),
                datetime.utcnow().isoformat(),
                inventory_qty,
                str(inventory_value),
                str(free_balance),
                str(total_balance),
                str(realized_pnl),
                str(unrealized_pnl)
            ])

    def record_trade(
        self,
        order_id: str,
        side: str,
        price: Decimal,
        quantity: int,
        commission: Decimal,
        pnl: Decimal,
    ):
        """记录成交"""
        with open(self.trades_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                int(datetime.utcnow().timestamp()),
                datetime.utcnow().isoformat(),
                order_id,
                side,
                str(price),
                quantity,
                str(commission),
                str(pnl)
            ])

    def save_config(self, config: Dict[str, Any]):
        """保存策略配置"""
        self.config_data = config
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2, default=str)

    def get_summary(self) -> str:
        """获取数据摘要"""
        orderbook_count = 0
        orders_count = 0
        trades_count = 0

        if self.orderbook_file.exists():
            with open(self.orderbook_file, 'r') as f:
                orderbook_count = sum(1 for _ in f) - 1  # 减去表头

        if self.orders_file.exists():
            with open(self.orders_file, 'r') as f:
                orders_count = sum(1 for _ in f) - 1

        if self.trades_file.exists():
            with open(self.trades_file, 'r') as f:
                trades_count = sum(1 for _ in f) - 1

        return f"""
数据记录摘要（会话 {self.session_id}）:
- 订单簿快照: {orderbook_count} 条
- 订单记录: {orders_count} 条
- 成交记录: {trades_count} 条
- 数据目录: {self.output_dir}
"""
