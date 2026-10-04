# FastAPI Course — Week 3: Integrating Streamlit and FastAPI

This folder implements the Week 3 exercises as a full-stack **Product Management System**.

The project builds on the FastAPI concepts from Week 2 and integrates a **Streamlit frontend**, **FastAPI backend**, **SQLite database**, **JWT authentication**, basic **performance optimization**, and cloud deployment.

The application was also deployed using **Render** for the FastAPI backend and **Streamlit Community Cloud** for the frontend.

---

## What the Assignment Asks For

| Day | Assignment expectation | Implementation |
| --- | --- | --- |
| 1 | Connect Streamlit to FastAPI, fetch data, and display it | `streamlit_app.py` calls `GET /products` using `requests` |
| 2 | Build a full-stack product-management application | Streamlit UI + FastAPI CRUD endpoints + SQLite |
| 3 | Add JWT/OAuth2-style authentication and protect routes | `/register`, `/login`, JWT bearer tokens, `Depends(current_user)` |
| 4 | Explore async I/O, caching, and database tuning | `/simulate-io`, product caching, SQLite category index |
| 5 | Deploy the full-stack application | FastAPI deployed on Render and frontend deployed on Streamlit Community Cloud |
| 6 | Dockerize the applications and use Docker Compose | Not included in this implementation |
| 7 | Project day: debug, polish, and add features | Filtering, error handling, tabs, authentication, and CRUD UI |
| 8 | Explore scaling and load balancing | Covered conceptually; production scaling requires deployment infrastructure |

---

# Architecture

The application follows a simple frontend-backend-database architecture.

```text
                    User
                     │
                     ▼
            Streamlit Frontend
                     │
                     │ HTTP / HTTPS
                     │ JSON
                     │
                     │ Authorization:
                     │ Bearer <JWT>
                     ▼
              FastAPI Backend
                     │
                     │ SQL
                     ▼
                  SQLite
```

The key architectural idea is that **Streamlit and FastAPI are separate applications**.

Streamlit does not access SQLite directly.

Instead:

```text
Streamlit
    │
    │ HTTP request
    ▼
FastAPI
    │
    │ SQL
    ▼
SQLite
```

FastAPI is responsible for:

- API routing
- request validation
- authentication
- business logic
- database access
- HTTP responses

Streamlit is responsible for:

- user input
- forms
- buttons
- displaying data
- sending API requests
- storing the JWT for the current session

---

# Technologies Used

| Technology | Purpose |
| --- | --- |
| Python | Application language |
| FastAPI | Backend REST API |
| Streamlit | Frontend user interface |
| SQLite | Application database |
| Pydantic | Request validation |
| PyJWT | JWT creation and verification |
| Requests | HTTP communication from Streamlit to FastAPI |
| Uvicorn | ASGI server for FastAPI |
| GitHub | Source-code repository |
| Render | FastAPI backend hosting |
| Streamlit Community Cloud | Streamlit frontend hosting |

---

# CRUD Operations

The application implements the four fundamental CRUD operations.

| Operation | HTTP Method | Endpoint |
| --- | --- | --- |
| Create | POST | `/products` |
| Read | GET | `/products` |
| Read One | GET | `/products/{product_id}` |
| Update | PUT | `/products/{product_id}` |
| Delete | DELETE | `/products/{product_id}` |

For example:

```text
GET /products
```

retrieves products, while:

```text
POST /products
```

creates a new product.

---

# JSON and Pydantic

The Streamlit frontend sends product information to FastAPI as JSON.

For example:

```json
{
    "name": "Laptop",
    "category": "Electronics",
    "price": 70000
}
```

Streamlit sends the request using:

```python
requests.post(
    f"{API_URL}/products",
    json=product_data
)
```

FastAPI validates the request using a Pydantic model:

```python
class Product(BaseModel):
    name: str
    category: str
    price: float
```

The request flow is:

```text
Streamlit
    │
    │ Python dictionary
    ▼
requests
    │
    │ JSON
    ▼
FastAPI
    │
    ▼
Pydantic validation
    │
    ▼
Endpoint logic
```

---

# SQLite Database

The application uses SQLite for persistence.

Two tables are created:

```text
users
products
```

The products table contains fields such as:

```text
id
name
category
price
```

The users table stores:

```text
id
username
password_hash
```

The database file:

```text
week3.db
```

is automatically created when the FastAPI application starts.

It is excluded from Git using `.gitignore`.

SQLite is suitable for this learning/demo application, although a production distributed application would normally use a database such as PostgreSQL.

---

# JWT Authentication

The application supports:

```text
Register
   ↓
Login
   ↓
JWT Token
   ↓
Protected API
```

A user first registers through:

```text
POST /register
```

and then logs in through:

```text
POST /login
```

After successful login, FastAPI returns a JWT access token.

Streamlit stores the token using:

```python
st.session_state.token
```

Protected requests include:

```text
Authorization: Bearer <token>
```

FastAPI verifies the token using:

```python
Depends(current_user)
```

before allowing protected operations such as:

```text
POST /products
PUT /products/{id}
DELETE /products/{id}
```

Therefore product modification requires authentication.

> Note: SHA-256 is used in this project only as a simple demonstration of password hashing. A production authentication system should use a password-hashing algorithm such as Argon2, bcrypt, or scrypt.

---

# Async I/O

The project contains:

```text
GET /simulate-io
```

which demonstrates asynchronous waiting using:

```python
async def simulate_io():
    await asyncio.sleep(3)
```

This represents operations where an application might be waiting for:

- another API
- network communication
- external services
- asynchronous database operations

An important distinction is that declaring a function with `async def` does not automatically make every operation inside it asynchronous.

The built-in Python `sqlite3` library used by this project is still synchronous.

---

# Caching

The product endpoint demonstrates simple in-memory caching.

The first request:

```text
GET /products
```

reads products from SQLite.

The result is temporarily cached.

A second request within the cache period can return the cached result instead of querying SQLite again.

Conceptually:

```text
First request

GET /products
      │
      ▼
   SQLite
      │
      ▼
    Cache
      │
      ▼
   Response


Next request

GET /products
      │
      ▼
    Cache
      │
      ▼
   Response
```

The cache is invalidated whenever products are created, updated, or deleted.

---

# Database Tuning

A SQLite index is created for:

```text
category
```

using:

```sql
CREATE INDEX IF NOT EXISTS
idx_products_category
ON products(category)
```

This demonstrates basic database optimization for a field frequently used for filtering.

For example:

```text
GET /products?category=grocery
```

---

# Scaling and Load Balancing

Scaling means increasing application capacity as traffic increases.

One common architecture is:

```text
                  Load Balancer
                       │
            ┌──────────┼──────────┐
            ▼          ▼          ▼
         FastAPI    FastAPI    FastAPI
         Instance   Instance   Instance
            1          2          3
```

The load balancer distributes incoming requests between backend instances.

This project does not implement production load balancing because it is a learning/demo application.

---

# Local Setup

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

---

## Run FastAPI

In Terminal 1:

```bash
python main.py
```

FastAPI runs locally at:

```text
http://127.0.0.1:8080
```

Swagger documentation:

```text
http://127.0.0.1:8080/docs
```

---

## Run Streamlit

In Terminal 2:

```bash
streamlit run streamlit_app.py
```

Streamlit normally opens at:

```text
http://localhost:8501
```

Locally the Streamlit frontend communicates with:

```text
http://127.0.0.1:8080
```

---

# Cloud Deployment

The application was deployed as two separate services.

```text
                     GitHub
                        │
              ┌─────────┴─────────┐
              │                   │
              ▼                   ▼
      Streamlit Cloud           Render
              │                   │
              │               FastAPI
              │                   │
              └──── HTTPS ───────►│
                                  │
                                  ▼
                                SQLite
```

## FastAPI Backend — Render

The FastAPI backend is deployed on Render.

Live backend:

https://fastapi-assignments.onrender.com

Swagger API documentation:

https://fastapi-assignments.onrender.com/docs

Render uses:

```bash
pip install -r requirements.txt
```

as the build command.

The FastAPI service starts using:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

The Render service uses:

```text
week3
```

as its root directory because the application is located inside the `week3/` folder of the repository.

---

## Streamlit Frontend — Streamlit Community Cloud

The Streamlit frontend is deployed separately using Streamlit Community Cloud.

The deployed application uses:

```text
week3/streamlit_app.py
```

as its main application file.

The frontend is configured with the FastAPI backend URL:

```text
https://fastapi-assignments.onrender.com
```

The deployed architecture therefore becomes:

```text
Browser
   │
   ▼
Streamlit Community Cloud
   │
   │ HTTPS REST requests
   ▼
Render
   │
   ▼
FastAPI
   │
   ▼
SQLite
```

This demonstrates that the frontend and backend can be independently deployed while still communicating through REST APIs.

---

# Suggested Test Flow

After starting or deploying the application:

1. Load the existing products.
2. Register a new user.
3. Log in.
4. Receive and store the JWT.
5. Create a new product.
6. Load products again and verify the product appears.
7. Update the product.
8. Delete the product.
9. Run the simulated I/O example.
10. Call `GET /products` twice within 10 seconds and observe the response source change from `database` to `cache`.

This exercises the complete application flow:

```text
User
 ↓
Streamlit
 ↓
HTTP / JSON
 ↓
FastAPI
 ↓
Authentication
 ↓
Pydantic
 ↓
SQLite
 ↓
FastAPI response
 ↓
Streamlit
 ↓
User
```

---

# Project Structure

```text
week3/
├── main.py
├── streamlit_app.py
├── requirements.txt
├── README.md
└── .gitignore
```

`week3.db` is generated automatically at runtime and is not committed to Git.

---

# Key Learning Outcomes

This project demonstrates:

- building REST APIs with FastAPI
- connecting a frontend to a backend using HTTP
- GET, POST, PUT, and DELETE requests
- CRUD application design
- JSON request and response handling
- Pydantic validation
- SQLite persistence
- JWT authentication
- FastAPI dependencies
- Streamlit session state
- async I/O fundamentals
- caching
- basic database indexing
- frontend/backend separation
- GitHub-based source control
- independent frontend and backend deployment

The central architecture learned during Week 3 is:

```text
Frontend
Streamlit
    │
    │ REST API
    │ HTTP + JSON
    ▼
Backend
FastAPI
    │
    │ SQL
    ▼
Database
SQLite
```

This same general architecture can later be extended by replacing Streamlit with frameworks such as React, SQLite with PostgreSQL, and the simple deployment with containerized and load-balanced infrastructure.