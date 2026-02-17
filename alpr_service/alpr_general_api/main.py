from Controllers import info, token, payment, subscription, user, auth
from Configs.dbconfig import engine, Base
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ALPR V2 API",
    description="Automatic License Plate Recognition Service API",
    version="2.0.0"
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://35.187.233.205",
    "http://35.187.233.205:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def read_root():
    return {"message": "The service is ready"}


@app.post("/testing/post")
async def testing_post():
    return {"message": "work"}

app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(token.router, prefix="/api/v1", tags=["tokens"])
app.include_router(info.router, prefix="/api/v1/info", tags=["users"])
app.include_router(payment.router, prefix="/api/v1/payment", tags=["payment"])
app.include_router(subscription.router,
                   prefix="/api/v1/subscription", tags=["subscription"])
app.include_router(user.router,
                   prefix="/api/v1/user", tags=["user"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8092,
                reload=True, log_level="debug")
