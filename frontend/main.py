import streamlit as st

# Import page components and navigation functions
from streamlit_navigation import navigation, get_current_page
from pages import register_page, login_page, chat_page


def main():
    # Render the sidebar navigation
    navigation()

    # Determine which page to display based on session state
    current_page = get_current_page()

    if current_page == 'register':
        register_page()
    elif current_page == 'login':
        login_page()
    elif current_page == 'chat':
        if 'refresh_token' in st.session_state:
            chat_page()
        else:
            st.error("Please log in to access the chat page.")
            login_page()
    else:
        st.error("Page not found")


if __name__ == "__main__":
    main()
