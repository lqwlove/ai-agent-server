"""
示例：异步向 MySQL 插入一行数据。

前置：项目根目录的 .env 已配置 DB_HOST / DB_PORT / DB_USERNAME / DB_PASSWORD / DB_DATABASE。

运行（任选其一）：
  poetry run python scripts/mysql_insert_example.py
  cd 项目根目录 && PYTHONPATH=. python scripts/mysql_insert_example.py

把下面的 SQL、表名、字段名改成你自己的。
"""
import asyncio

from sqlalchemy import text

from app.utils.mysql_utils import async_engine, async_session


async def main() -> None:
    async with async_session() as session:
        # 使用参数绑定，避免拼接 SQL 注入
        async with session.begin():
            await session.execute(
                text(
                    """
                    INSERT INTO your_table_name (column_a, column_b)
                    VALUES (:column_a, :column_b)
                    """
                ),
                {
                    "column_a": "示例值A",
                    "column_b": "示例值B",
                },
            )
        # session.begin() 退出时自动 commit；异常则 rollback

    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
