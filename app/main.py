from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.env import env
import datetime
from app.routes import routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Server started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    yield
    print(
        f"Server destroyed at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


app = FastAPI(
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

for add_route_func in routes:
    add_route_func(app)

if env.server_enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
