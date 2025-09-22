import os

from fastapi import FastAPI, Depends

from Controllers import web_socket_images
from Configs.dbconfig import init_db, engine
app = FastAPI()

# WebSocket endpoint using token validation and database session


app.include_router(web_socket_images.router, prefix="/ws/v1")


@app.on_event("startup")
async def on_startup():
    await init_db()


@app.on_event("shutdown")
async def on_shutdown():
    await engine.dispose()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8090,
                reload=True, log_level="debug")
