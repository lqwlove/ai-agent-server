from app.config.env import env
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.params import Depends
from typing import Annotated
from sqlalchemy import text


DATABASE_URL = f"mysql+asyncmy://{env.db_username}:{env.db_password}@{env.db_host}:{env.db_port}/{env.db_database}?charset=utf8mb4"

async_engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=5,
    pool_recycle=60,
    pool_pre_ping=True,
    echo=True,
    future=True,
)

# 使用这个 Session 工厂
async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


# 作用：用于在接口中注入得到会话实例对象session，在接口执行完毕之后，自动执行close动作关闭会话
async def get_async_session() -> AsyncSession:
    async with async_session() as session:
        yield session


# 作为类型使用，直接在接口参数中注入得到session会话实例对象
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


# 用于启动服务的时候检查数据库连接是否正常
async def check_database_connection():
    """检查数据库连接是否正常"""
    try:
        async with async_engine.begin() as conn:
            print("Connecting Mysql...")
            await conn.execute(text("select 1"))
            # 打印连接成功信息及连接URL
            print("✅ MySql connection successful：", DATABASE_URL)
    except Exception as e:
        # 打印连接失败信息及错误详情
        print(f"❌ Database connection failed: {e}")
        # 重新抛出异常，让上层处理
        raise e
    return async_engine
