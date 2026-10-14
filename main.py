import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .ai import ask_ai
from .auth import create_token, current_user_id, hash_password, verify_password
from .database import get_conn, init_db

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="SupportDesk AI", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------- schemas ----------
class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=100)


class BotIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    instructions: str = Field(min_length=5, max_length=4000)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


# ---------- helpers ----------
def get_owned_bot(conn, bot_id: int, user_id: int):
    bot = conn.execute(
        "SELECT * FROM bots WHERE id = ? AND user_id = ?", (bot_id, user_id)
    ).fetchone()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot


# ---------- pages ----------
@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


# ---------- auth ----------
@app.post("/api/register")
def register(data: Credentials):
    email = data.email.strip().lower()
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, hash_password(data.password)),
            )
            user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    return {"token": create_token(user_id)}


@app.post("/api/login")
def login(data: Credentials):
    email = data.email.strip().lower()
    with get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Wrong email or password")
    return {"token": create_token(user["id"])}


# ---------- bots ----------
@app.get("/api/bots")
def list_bots(user_id: int = Depends(current_user_id)):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, instructions FROM bots WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


@app.post("/api/bots")
def create_bot(data: BotIn, user_id: int = Depends(current_user_id)):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO bots (user_id, name, instructions) VALUES (?, ?, ?)",
            (user_id, data.name.strip(), data.instructions.strip()),
        )
    return {"id": cur.lastrowid, "name": data.name, "instructions": data.instructions}


@app.delete("/api/bots/{bot_id}")
def delete_bot(bot_id: int, user_id: int = Depends(current_user_id)):
    with get_conn() as conn:
        get_owned_bot(conn, bot_id, user_id)
        conn.execute("DELETE FROM bots WHERE id = ?", (bot_id,))
    return {"ok": True}


# ---------- chat ----------
@app.get("/api/bots/{bot_id}/messages")
def get_messages(bot_id: int, user_id: int = Depends(current_user_id)):
    with get_conn() as conn:
        get_owned_bot(conn, bot_id, user_id)
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE bot_id = ? ORDER BY id",
            (bot_id,),
        ).fetchall()
    return [dict(r) for r in rows]


@app.post("/api/bots/{bot_id}/chat")
def chat(bot_id: int, data: ChatIn, user_id: int = Depends(current_user_id)):
    with get_conn() as conn:
        bot = get_owned_bot(conn, bot_id, user_id)
        conn.execute(
            "INSERT INTO messages (bot_id, role, content) VALUES (?, 'user', ?)",
            (bot_id, data.message),
        )
        history = [
            dict(r)
            for r in conn.execute(
                "SELECT role, content FROM messages WHERE bot_id = ? ORDER BY id",
                (bot_id,),
            ).fetchall()
        ]

    reply = ask_ai(bot["instructions"], history)

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (bot_id, role, content) VALUES (?, 'assistant', ?)",
            (bot_id, reply),
        )
    return {"reply": reply}