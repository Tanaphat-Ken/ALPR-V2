import os
from fastapi import FastAPI, Request
from Middlewares.token_auth import TokenAuthMiddleware
from Configs.dbconfig import init_db, engine, get_db, DATABASE_URL
from Controllers import image
from fastapi.middleware.cors import CORSMiddleware

IS_DEV = os.getenv("APP_ENV", "production") == "development"

app = FastAPI(
    root_path="/api/image",
    docs_url="/docs" if IS_DEV else None,
    redoc_url="/redoc" if IS_DEV else None,
    openapi_url="/openapi.json" if IS_DEV else None,
)

app.add_middleware(TokenAuthMiddleware, db_url=DATABASE_URL)
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()


@app.on_event("shutdown")
async def on_shutdown():
    await engine.dispose()


async def get_request_session(request: Request):
    db_session = await get_db().__anext__()  # Fetch the session
    request.state.db = db_session  # Attach session to request state
    try:
        yield db_session  # Provide the session
    finally:
        await db_session.close()  # Ensure session is closed after the request


@app.middleware("http")
async def add_session_to_request(request: Request, call_next):
    # Inject the session into request.state.db
    # async for db_session in get_request_session(request):
    #     request.state.db = db_session
    #     response = await call_next(request)
    #     return response
    response = await call_next(request)
    return response


@app.get("/secure-data")
async def secure_data():
    return {"message": "This is a protected route, and you have valid authentication!"}


app.include_router(image.router, prefix="/api/v1/images")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8089,
                reload=True, log_level="debug")
