#!/usr/bin/env python3
"""
使用富途 OpenAPI（需本机运行 OpenD）拉取指定标的的历史日线。

前置条件：
  1. 安装：pip install futu-api pandas
  2. 启动富途牛牛客户端中的 OpenAPI（OpenD），默认地址 127.0.0.1:11111
  3. 写入 MySQL：项目根目录配置好 .env，并加 --insert-db（表 trade_stock_daily 需已存在）

标的代码示例：美股 US.AAPL、港股 HK.00700、A 股 SH.600519。
若你说的「figma」指具体股票，请在富途客户端行情里查看完整代码并传入 --code。
（Figma 公司本身未以 FIGMA 代码单独上市；若指美股 FIG 等 ETF，请用对应代码如 US.FIG。）
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from futu import OpenQuoteContext
    from futu.common.constant import RET_OK
    from futu.common.constant import AuType
    from futu.common.constant import KLType
except ImportError as e:
    raise SystemExit(
        "请先安装依赖：pip install futu-api pandas\n" f"导入失败：{e}"
    ) from e


def fetch_daily_kline(
    code: str,
    start: str,
    end: str,
    *,
    host: str = "127.0.0.1",
    port: int = 11111,
    autype: AuType = AuType.QFQ,
    max_count: int = 1000,
) -> pd.DataFrame:
    """分页请求历史日 K，合并为单个 DataFrame。"""
    frames: list[pd.DataFrame] = []
    page_req_key = None

    quote_ctx = OpenQuoteContext(host=host, port=port)
    try:
        while True:
            ret, data, page_req_key = quote_ctx.request_history_kline(
                code=code,
                start=start,
                end=end,
                ktype=KLType.K_DAY,
                autype=autype,
                max_count=max_count,
                page_req_key=page_req_key,
            )
            if ret != RET_OK:
                raise RuntimeError(f"request_history_kline 失败: {data}")

            if data is not None and not data.empty:
                frames.append(data)

            if not page_req_key:
                break
    finally:
        quote_ctx.close()

    if not frames:
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True)
    if "time_key" in out.columns:
        out = out.sort_values("time_key").drop_duplicates(
            subset=["time_key"], keep="last"
        )
    return out.reset_index(drop=True)


def _is_null(v: object) -> bool:
    if v is None:
        return True
    try:
        return bool(pd.isna(v))
    except (TypeError, ValueError):
        return False


def _f_or_none(v: object) -> float | None:
    if _is_null(v):
        return None
    return float(v)


def _i_or_none(v: object) -> int | None:
    if _is_null(v):
        return None
    return int(round(float(v)))


def _trade_date_from_row(time_key: object) -> date:
    if hasattr(time_key, "date"):
        d = time_key.date()
        if isinstance(d, date):
            return d
    ts = pd.to_datetime(time_key, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"无法解析交易日期: {time_key!r}")
    py_dt = ts.to_pydatetime()
    return py_dt.date()


def dataframe_to_trade_models(df: pd.DataFrame, fallback_code: str) -> list[Any]:
    """富途日 K DataFrame -> TradeStockDailyModel 实例列表（延后 import 避免未装依赖时影响 CSV 导出）。"""
    from app.models.TradeStockDailyModel import TradeStockDailyModel

    rows: list[TradeStockDailyModel] = []
    for rec in df.to_dict("records"):
        code = rec.get("code")
        stock_code = (
            str(code).strip()
            if code is not None and str(code).strip()
            else fallback_code
        )
        rows.append(
            TradeStockDailyModel(
                stock_code=stock_code,
                trade_date=_trade_date_from_row(rec["time_key"]),
                open_price=_f_or_none(rec.get("open")),
                high_price=_f_or_none(rec.get("high")),
                low_price=_f_or_none(rec.get("low")),
                close_price=_f_or_none(rec.get("close")),
                volume=_i_or_none(rec.get("volume")),
                amount=_i_or_none(rec.get("turnover")),
                turnover_rate=_f_or_none(rec.get("turnover_rate")),
            )
        )
    return rows


async def _insert_models(models: list[Any]) -> int:
    from app.utils.mysql_utils import async_engine, async_session

    if not models:
        return 0
    async with async_session() as session:
        session.add_all(models)
        await session.commit()
    await async_engine.dispose()
    return len(models)


def insert_dataframe_to_db(df: pd.DataFrame, stock_code: str) -> int:
    """
    将拉取结果一次性写入 trade_stock_daily（条数与本次拉取一致）。
    重复执行且未建唯一索引时可能产生重复行；可在库中对 (stock_code, trade_date) 建唯一约束后再做 upsert。
    """
    models = dataframe_to_trade_models(df, stock_code)
    return asyncio.run(_insert_models(models))


def main() -> None:
    today = date.today()
    default_end = min(date(today.year, 12, 31), today).strftime("%Y-%m-%d")
    default_start = f"{today.year}-01-01"

    parser = argparse.ArgumentParser(description="富途 OpenAPI 拉取历史日线")
    parser.add_argument(
        "--code",
        type=str,
        default="US.FIG",
        help="富途标的代码，例如 US.AAPL、HK.00700（默认 US.FIG，可按需修改）",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="指定自然年（设置后 start/end 为该年 1/1 至今天与该年末日的较早者，优先级高于 --start/--end）",
    )
    parser.add_argument(
        "--start", type=str, default=default_start, help="开始日期 YYYY-MM-DD"
    )
    parser.add_argument(
        "--end", type=str, default=default_end, help="结束日期 YYYY-MM-DD"
    )
    parser.add_argument("--host", type=str, default="127.0.0.1", help="OpenD 地址")
    parser.add_argument("--port", type=int, default=11111, help="OpenD 端口")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="",
        help="保存路径（csv）；默认 scripts/data/<code>_daily_<start>_<end>.csv",
    )
    parser.add_argument(
        "--insert-db",
        action="store_true",
        help="拉取并保存 CSV 后，将本次全部行写入 MySQL 表 trade_stock_daily（依赖 .env）",
    )
    args = parser.parse_args()

    if args.year is not None:
        y_end = min(date(args.year, 12, 31), today)
        start = f"{args.year}-01-01"
        end = y_end.strftime("%Y-%m-%d")
    else:
        start = args.start
        end = args.end

    print(f"请求 {args.code} 日线 {start} ~ {end} …")
    df = fetch_daily_kline(args.code, start, end, host=args.host, port=args.port)

    if df.empty:
        print(
            "未返回任何数据（请检查代码权限、OpenD 是否登录、日期区间内是否有交易日）。"
        )
        return

    print(df.head(3).to_string())
    print("…")

    if args.insert_db:
        n = insert_dataframe_to_db(df, args.code)
        print(f"已写入数据库 trade_stock_daily：{n} 条")


if __name__ == "__main__":
    main()
