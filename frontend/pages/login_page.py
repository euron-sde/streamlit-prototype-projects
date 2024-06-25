import streamlit as st
import requests

LOGIN_URL = "http://localhost:9000/users/tokens"


def login_user(email, password):
    try:
        response = requests.post(LOGIN_URL, json={"email": email, "password": password})
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        st.error(f"Login request failed: {e}")
        return None


def login_page():
    st.title("Login")
    login_email = st.text_input("Login Email")
    login_password = st.text_input("Login Password", type="password")
    if st.button(label="Login", key="login_button"):  # Added unique key argument
        login_response = login_user(login_email, login_password)
        if login_response and login_response.status_code == 200:
            st.success("Logged in successfully!")
            tokens = login_response.json()
            st.session_state.refresh_token = tokens.get("refresh_token")
            st.session_state.access_token = tokens.get("access_token")
        else:
            st.error("Login failed!")
