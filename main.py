from app.config.env import env


if __name__ == "__main__":
    import uvicorn

    port = env.server_port
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
