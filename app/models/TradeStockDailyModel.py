from datetime import date

from sqlmodel import Field, SQLModel


class TradeStockDailyModel(SQLModel, table=True):
    __tablename__ = "trade_stock_daily"

    id: int | None = Field(default=None, primary_key=True, description="主键")
    stock_code: str = Field(max_length=255, default="", description="股票代码")
    trade_date: date = Field(description="交易日期")
    open_price: float = Field(default=None, description="开盘价")
    high_price: float = Field(default=None, description="最高价")
    low_price: float = Field(default=None, description="最低价")
    close_price: float = Field(default=None, description="收盘价")
    volume: int = Field(default=None, description="成交量")
    amount: int = Field(default=None, description="成交额")
    turnover_rate: float = Field(default=None, description="换手率")
