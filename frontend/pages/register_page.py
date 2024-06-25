import streamlit as st
import requests

REGISTER_URL = "http://localhost:9000/users"


def register_user(email, password):
    try:
        response = requests.post(REGISTER_URL, json={"email": email, "password": password})
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        st.error(f"Registration request failed: {e}")
        return None


def register_page():
    st.title("Register")
    register_email = st.text_input("Register Email")
    register_password = st.text_input("Register Password", type="password")
    if st.button(label="Register", key="register_button"):  # Added unique key argument
        register_response = register_user(register_email, register_password)
        if register_response and register_response.status_code == 201:
            st.success("User registered successfully!")
        else:
            st.error("Registration failed!")
