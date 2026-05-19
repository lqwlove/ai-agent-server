from fastapi import FastAPI


def add_test_route(app: FastAPI):
    @app.get("/test")
    async def chat():
        return {"message": "Hello, World!"}
