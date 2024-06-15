import streamlit as st


def set_page(page):
    st.session_state.current_page = page


def get_current_page():
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'register'
    return st.session_state.current_page


def navigation():
    st.sidebar.title("Navigation")
    if st.sidebar.button("Register"):
        set_page('register')
    if st.sidebar.button("Login"):
        set_page('login')
    if 'refresh_token' in st.session_state and st.sidebar.button("Chat"):
        set_page('chat')
