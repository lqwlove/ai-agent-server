"""
示例表模型。使用前在 MySQL 中建表，例如：

CREATE TABLE demo_books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    is_published TINYINT(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

或开发环境可用 SQLModel.metadata + create_all（见 scripts/sync_demo_tables.py）。
"""
from sqlmodel import Field, SQLModel


class Book(SQLModel, table=True):
    __tablename__ = "demo_books"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255, index=True)
    is_published: bool = Field(default=False)
