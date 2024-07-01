import streamlit as st
import requests


CHAT_START_URL = "http://localhost:9000/chat/start"
ADD_MESSAGE_URL = "http://localhost:9000/chat"
ALL_CHAT_URL = "http://localhost:9000/allChat"


def set_cookie_in_header(refresh_token):
    from http.cookies import SimpleCookie  # type: ignore
    cookies = SimpleCookie()
    cookies["refreshToken"] = refresh_token
    cookie_header = cookies.output(header="", sep=";").strip()
    return {"Cookie": cookie_header}


def start_chat(refresh_token):
    try:
        headers = set_cookie_in_header(refresh_token)
        response = requests.post(CHAT_START_URL, headers=headers)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        st.error(f"Start chat request failed: {e}")
        return None


def add_message_to_chat(refresh_token, message, is_image=False, image_data=None, stream=False):
    try:
        headers = set_cookie_in_header(refresh_token)
        data = {"message": message, "is_image": is_image, "stream": stream}
        if is_image:
            data["image_data"] = image_data
        response = requests.post(ADD_MESSAGE_URL, headers=headers, json=data)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        st.error(f"Add message request failed: {e}")
        return None


def get_all_chat(refresh_token):
    try:
        headers = set_cookie_in_header(refresh_token)
        response = requests.get(ALL_CHAT_URL, headers=headers)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        st.error(f"Get all chat request failed: {e}")
        return None


def display_chat_messages(messages):
    for message in messages:
        if message['role'] == 'user':
            with st.chat_message("user"):
                st.markdown(message['message'])
        else:
            with st.chat_message("assistant"):
                st.markdown(message['message'])


def load_chat_messages(refresh_token):
    get_all_chat_response = get_all_chat(refresh_token)
    if get_all_chat_response and get_all_chat_response.status_code == 200:
        return get_all_chat_response.json()
    st.error("Failed to retrieve chat messages!")
    return []  # Ensure a list is returned


def chat_page():
    st.title("Chat")

    if 'refresh_token' not in st.session_state:
        st.error("Please log in to access the chat page.")
        return

    if 'displayed_message_ids' not in st.session_state:
        st.session_state.displayed_message_ids = set()
        st.session_state.messages = []

    if st.button("Start Chat"):
        start_chat_response = start_chat(st.session_state.refresh_token)
        if start_chat_response and start_chat_response.status_code == 200:
            st.success("Chat started successfully!")
        else:
            st.error("Failed to start chat!")

    if chat_messages := load_chat_messages(st.session_state.refresh_token):
        display_chat_messages(chat_messages)
        st.session_state.messages = chat_messages

    if chat_message := st.chat_input("Type your message here..."):
        add_message_response = add_message_to_chat(st.session_state.refresh_token, chat_message)
        if add_message_response and add_message_response.status_code == 200:
            st.session_state.messages.append({"role": "user", "message": chat_message})
            with st.chat_message("user"):
                st.markdown(chat_message)

            assistant_message = add_message_response.json().get("content", "")
            with st.chat_message("assistant"):
                st.markdown(assistant_message)
            st.session_state.messages.append({"role": "assistant", "message": assistant_message})
        else:
            st.error("Failed to send message!")
