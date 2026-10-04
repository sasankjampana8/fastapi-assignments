"""Week 3: Streamlit + FastAPI full-stack product management app.

Run locally:
    python main.py
in terminal 1, then:
    streamlit run streamlit_app.py
in terminal 2.
"""

import asyncio
import hashlib
import os
import sqlite3
import time
from collections.abc import Iterator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field

DB_PATH = Path(__file__).resolve().parent / "week3.db"
SECRET_KEY = os.getenv("JWT_SECRET", "week3-learning-secret-change-me")
ALGORITHM = "HS256"
TOKEN_MINUTES = 30

# A tiny in-memory cache for the Week 3 performance exercise.
PRODUCT_CACHE: dict[str, object] = {"data": None, "expires_at": 0.0}
CACHE_SECONDS = 10


def init_db() -> None:
    """Create the two tables and seed a couple of products on first run."""
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL CHECK(price >= 0)
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )
        count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            db.executemany(
                "INSERT INTO products (name, category, price) VALUES (?, ?, ?)",
                [
                    ("Notebook", "stationery", 120.0),
                    ("Coffee", "grocery", 250.0),
                ],
            )
        # Index = a simple database-tuning example for category filtering.
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Week 3 Product Management API", lifespan=lifespan)


class Product(BaseModel):
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    price: float = Field(ge=0)


class Credentials(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=4)


def get_db() -> Iterator[sqlite3.Connection]:
    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()


def invalidate_product_cache() -> None:
    PRODUCT_CACHE["data"] = None
    PRODUCT_CACHE["expires_at"] = 0.0


# SHA-256 is used here only to demonstrate "hash, don't store plaintext".
# Real applications should use Argon2/bcrypt/scrypt instead.
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


@app.get("/health")
def health():
    return {"message": "Week 3 API is running"}


# Day 1: endpoint consumed by Streamlit.
# Day 4: simple time-based cache.
@app.get("/products")
def list_products(
    category: str | None = None,
    db: sqlite3.Connection = Depends(get_db),
):
    now = time.time()

    # Cache only the unfiltered list to keep the example easy to understand.
    if category is None and PRODUCT_CACHE["data"] is not None:
        if now < float(PRODUCT_CACHE["expires_at"]):
            return {"source": "cache", "products": PRODUCT_CACHE["data"]}

    if category:
        rows = db.execute(
            "SELECT * FROM products WHERE category = ? ORDER BY id", (category,)
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM products ORDER BY id").fetchall()

    products = [dict(row) for row in rows]

    if category is None:
        PRODUCT_CACHE["data"] = products
        PRODUCT_CACHE["expires_at"] = now + CACHE_SECONDS

    return {"source": "database", "products": products}


@app.get("/products/{product_id}")
def get_product(product_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(row)


# Day 3: registration + login + JWT.
@app.post("/register", status_code=201)
def register(credentials: Credentials, db: sqlite3.Connection = Depends(get_db)):
    try:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (credentials.username, hash_password(credentials.password)),
        )
        db.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Username already exists") from exc
    return {"message": "User registered"}


@app.post("/login")
def login(credentials: Credentials, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT * FROM users WHERE username = ?", (credentials.username,)
    ).fetchone()

    if row is None or row["password_hash"] != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {
        "access_token": create_access_token(credentials.username),
        "token_type": "bearer",
    }


# Day 2: CRUD. Write operations are protected by JWT for Day 3.
@app.post("/products", status_code=201)
def create_product(
    product: Product,
    username: str = Depends(current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    cursor = db.execute(
        "INSERT INTO products (name, category, price) VALUES (?, ?, ?)",
        (product.name, product.category, product.price),
    )
    db.commit()
    invalidate_product_cache()
    row = db.execute(
        "SELECT * FROM products WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return dict(row)


@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    product: Product,
    username: str = Depends(current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    existing = db.execute(
        "SELECT id FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if existing is None:
        raise HTTPException(status_code=404, detail="Product not found")

    db.execute(
        """
        UPDATE products
        SET name = ?, category = ?, price = ?
        WHERE id = ?
        """,
        (product.name, product.category, product.price, product_id),
    )
    db.commit()
    invalidate_product_cache()
    return {"message": "Product updated"}


@app.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    username: str = Depends(current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    existing = db.execute(
        "SELECT id FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if existing is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    invalidate_product_cache()


# Day 4: async I/O demonstration.
@app.get("/simulate-io")
async def simulate_io():
    await asyncio.sleep(3)
    return {"message": "Finished a simulated 3-second I/O wait"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
