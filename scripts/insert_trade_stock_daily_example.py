"""
使用 TradeStockDailyModel 向 MySQL 插入数据。

前置：表 trade_stock_daily 已存在（或你用 Alembic / 手工 SQL 建表）。
项目根目录运行：
  PYTHONPATH=. python scripts/insert_trade_stock_daily_example.py
"""
import asyncio
from datetime import date

from app.models.TradeStockDailyModel import TradeStockDailyModel
from app.utils.mysql_utils import async_engine, async_session


async def main() -> None:
    row = TradeStockDailyModel(
        stock_code="600000",
        trade_date=date(2026, 5, 18),
        open_price=10.5,
        high_price=10.8,
        low_price=10.4,
        close_price=10.7,
        volume=1_000_000,
        amount=10_700_000,
        turnover_rate=0.012,
    )

    async with async_session() as session:
        session.add(row)
        await session.commit()
        await session.refresh(row)
        print("插入成功, id =", row.id)

    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
