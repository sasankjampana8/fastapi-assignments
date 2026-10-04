"""Week 3 Streamlit frontend.

Local use:
    streamlit run streamlit_app.py

By default it expects FastAPI at http://127.0.0.1:8080.
For a hosted frontend, set API_URL to the URL of a separately hosted FastAPI API.
"""

import os

import requests
import streamlit as st

# API_URL = os.getenv("API_URL", "http://127.0.0.1:8080").rstrip("/")
API_URL = st.secrets.get(
    "API_URL",
    "http://127.0.0.1:8080"
).rstrip("/")

st.set_page_config(page_title="Week 3 Product Manager", page_icon="📦")
st.title("📦 Week 3 Product Management")
st.caption("Streamlit frontend consuming a FastAPI backend over HTTP")

if "token" not in st.session_state:
    st.session_state.token = None


def auth_headers() -> dict[str, str]:
    if not st.session_state.token:
        return {}
    return {"Authorization": f"Bearer {st.session_state.token}"}


def show_error(response: requests.Response) -> None:
    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text
    st.error(f"{response.status_code}: {detail}")


# Day 1: fetch FastAPI data and show it in Streamlit.
st.header("1. View products")
category = st.text_input("Optional category filter", key="filter_category")

if st.button("Load products"):
    try:
        params = {"category": category} if category.strip() else {}
        response = requests.get(f"{API_URL}/products", params=params, timeout=10)
        if response.ok:
            data = response.json()
            st.caption(f"Response source: {data['source']}")
            st.dataframe(data["products"], use_container_width=True)
        else:
            show_error(response)
    except requests.RequestException as exc:
        st.error(f"Could not reach FastAPI: {exc}")


# Day 3: registration and login.
st.header("2. Authentication")
auth_tab, register_tab = st.tabs(["Login", "Register"])

with register_tab:
    reg_user = st.text_input("New username", key="reg_user")
    reg_password = st.text_input("New password", type="password", key="reg_password")
    if st.button("Register"):
        try:
            response = requests.post(
                f"{API_URL}/register",
                json={"username": reg_user, "password": reg_password},
                timeout=10,
            )
            if response.ok:
                st.success("Registered. You can now log in.")
            else:
                show_error(response)
        except requests.RequestException as exc:
            st.error(f"Could not reach FastAPI: {exc}")

with auth_tab:
    login_user = st.text_input("Username", key="login_user")
    login_password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        try:
            response = requests.post(
                f"{API_URL}/login",
                json={"username": login_user, "password": login_password},
                timeout=10,
            )
            if response.ok:
                st.session_state.token = response.json()["access_token"]
                st.success("Logged in. Protected CRUD controls are enabled.")
            else:
                show_error(response)
        except requests.RequestException as exc:
            st.error(f"Could not reach FastAPI: {exc}")

    if st.session_state.token and st.button("Logout"):
        st.session_state.token = None
        st.rerun()


# Day 2 + Day 3: full-stack protected CRUD.
st.header("3. Manage products")

if not st.session_state.token:
    st.info("Log in to create, update, or delete products.")
else:
    create_tab, update_tab, delete_tab = st.tabs(["Create", "Update", "Delete"])

    with create_tab:
        name = st.text_input("Name", key="create_name")
        product_category = st.text_input("Category", key="create_category")
        price = st.number_input("Price", min_value=0.0, key="create_price")

        if st.button("Create product"):
            try:
                response = requests.post(
                    f"{API_URL}/products",
                    json={"name": name, "category": product_category, "price": price},
                    headers=auth_headers(),
                    timeout=10,
                )
                if response.ok:
                    st.success(f"Created product #{response.json()['id']}")
                else:
                    show_error(response)
            except requests.RequestException as exc:
                st.error(f"Could not reach FastAPI: {exc}")

    with update_tab:
        update_id = st.number_input(
            "Product ID", min_value=1, step=1, key="update_id"
        )
        update_name = st.text_input("New name", key="update_name")
        update_category = st.text_input("New category", key="update_category")
        update_price = st.number_input(
            "New price", min_value=0.0, key="update_price"
        )

        if st.button("Update product"):
            try:
                response = requests.put(
                    f"{API_URL}/products/{int(update_id)}",
                    json={
                        "name": update_name,
                        "category": update_category,
                        "price": update_price,
                    },
                    headers=auth_headers(),
                    timeout=10,
                )
                if response.ok:
                    st.success("Product updated")
                else:
                    show_error(response)
            except requests.RequestException as exc:
                st.error(f"Could not reach FastAPI: {exc}")

    with delete_tab:
        delete_id = st.number_input(
            "Product ID", min_value=1, step=1, key="delete_id"
        )
        if st.button("Delete product"):
            try:
                response = requests.delete(
                    f"{API_URL}/products/{int(delete_id)}",
                    headers=auth_headers(),
                    timeout=10,
                )
                if response.status_code == 204:
                    st.success("Product deleted")
                else:
                    show_error(response)
            except requests.RequestException as exc:
                st.error(f"Could not reach FastAPI: {exc}")


# Day 4: basic performance/async demonstration.
st.header("4. Performance demo")
if st.button("Run simulated I/O"):
    with st.spinner("Waiting for the API..."):
        try:
            response = requests.get(f"{API_URL}/simulate-io", timeout=10)
            if response.ok:
                st.success(response.json()["message"])
            else:
                show_error(response)
        except requests.RequestException as exc:
            st.error(f"Could not reach FastAPI: {exc}")
