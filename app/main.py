# app/main.py (add after creating FastAPI app)
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import chat as chat_router
from app.api.routes import flashcard as flashcard_router
from app.api.routes import user as user_router
from app.database.init_db import create_tables
from app.scripts.user_create import create_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    import app.models as models  # noqa: F401, F403

    await create_tables()  # Initializes tables
    await create_user("tester@test.com", "testpass", True)
    print("✅ Application started and database tables created!")
    yield
    print("🛑 Application shutting down!")


app = FastAPI(lifespan=lifespan)
app.include_router(user_router.router)
app.include_router(flashcard_router.router)
app.include_router(chat_router.router)


@app.get("/")
async def home(request: Request):
    return JSONResponse(content={"home": "home"})
