# FastAPI Course — Week 3: Integrating Streamlit and FastAPI

This folder implements the Week 3 exercises as one product-management project. It continues the product API idea from Week 2 and adds a Streamlit frontend, JWT authentication, performance examples, and a more complete full-stack workflow.

## What the assignment asks for

| Day | Assignment expectation | Where it is implemented |
| --- | --- | --- |
| 1 | Connect Streamlit to FastAPI, fetch data, display it as a table/chart | `streamlit_app.py` → **View products**, calling `GET /products` |
| 2 | Build a full-stack product app; submit and fetch product data; CRUD | Streamlit **Manage products** + FastAPI product GET/POST/PUT/DELETE routes |
| 3 | Add JWT/OAuth2-style authentication and protect product-management APIs | `/register`, `/login`, JWT bearer token, `Depends(current_user)` |
| 4 | Use async I/O, caching and DB tuning; benchmark performance | `/simulate-io`, 10-second product cache, SQLite category index |
| 5 | Deploy FastAPI + Streamlit | **Intentionally excluded from this ZIP at your request** |
| 6 | Dockerize FastAPI and Streamlit and orchestrate with Docker Compose | Not included because this submission is being kept simple and deployment is excluded |
| 7 | Project day: debug/polish and add features such as filters | Category filter, error handling, tabs, authenticated CRUD |
| 8 | Scaling/load balancing and optimization for larger load | Explained conceptually below; production load balancing needs deployment infrastructure |

## Architecture

```text
User
  |
  v
Streamlit frontend
  |
  | HTTP requests + JSON
  | Authorization: Bearer <JWT> for protected writes
  v
FastAPI backend
  |
  | SQL
  v
SQLite
```

The key Week 3 idea is that Streamlit and FastAPI are separate applications. Streamlit does not directly read the database. It calls the FastAPI API with `requests`, and FastAPI owns validation, authentication and database access.

## Core concepts

### GET vs POST vs PUT vs DELETE

- `GET /products` reads products.
- `POST /products` creates a product.
- `PUT /products/{id}` updates a product.
- `DELETE /products/{id}` removes a product.

Together these form CRUD: Create, Read, Update and Delete.

### JSON and Pydantic

Streamlit sends a Python dictionary with `requests.post(..., json=data)`. It travels over HTTP as JSON. FastAPI converts the JSON into the `Product` Pydantic model and validates required fields and types before the endpoint runs.

### JWT authentication

Registration stores a password hash. Login checks the credentials and returns a signed JWT. Streamlit keeps that token in `st.session_state` and sends it in the `Authorization` header:

```text
Authorization: Bearer <token>
```

`Depends(current_user)` verifies the token before protected POST/PUT/DELETE endpoints execute.

The SHA-256 password hash in this learning project is deliberately simple. Production apps should use Argon2/bcrypt/scrypt and keep the JWT secret in a secret manager/environment variable.

### Async

`GET /simulate-io` uses `async def` and `await asyncio.sleep(3)` to demonstrate non-blocking waiting. `async` is most useful when the work being awaited is asynchronous I/O. The built-in `sqlite3` library itself is synchronous.

### Caching and DB tuning

The unfiltered product list is cached in memory for 10 seconds. The cache is invalidated whenever a product changes. SQLite also gets an index on `category`, which is a basic example of database tuning for a frequently filtered column.

### Scaling and load balancing

Scaling means running more application capacity as traffic grows. Load balancing distributes requests across multiple backend instances. Streamlit Community Cloud is useful for hosting a Streamlit frontend, but it is not a substitute for a separately deployed/load-balanced FastAPI service.

## Run locally

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Terminal 1:

```bash
python main.py
```

FastAPI runs at `http://127.0.0.1:8080`. Swagger docs are at `http://127.0.0.1:8080/docs`.

Terminal 2:

```bash
streamlit run streamlit_app.py
```

The Streamlit UI normally opens at `http://localhost:8501`.

## GitHub and Streamlit Community Cloud

Yes, this folder can be pushed to GitHub. However, **deploying only `streamlit_app.py` to Streamlit Community Cloud does not automatically deploy the FastAPI backend**. The default `API_URL` is `http://127.0.0.1:8080`, which only works when FastAPI is running on the same machine.

For a real hosted version, deploy FastAPI separately and set an `API_URL` environment variable for the Streamlit app to that public backend URL. If the course only needs a GitHub submission and local demonstration, the two-terminal local setup is enough.

Also remember that SQLite is appropriate for this learning project but is not a good shared production database for horizontally scaled backend instances.

## Suggested test flow

1. Start FastAPI and Streamlit.
2. Load products.
3. Register a user.
4. Log in and obtain a JWT.
5. Create a product.
6. Load products again.
7. Update that product.
8. Delete it.
9. Click **Run simulated I/O**.
10. Call `GET /products` twice quickly and observe `source` change from `database` to `cache`.

## Files

```text
week3/
├── main.py
├── streamlit_app.py
├── requirements.txt
├── README.md
└── .gitignore
```

`week3.db` is created automatically on first run and is ignored by Git.
