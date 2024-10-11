import sys
import os

# Add the parent directory (Big Data assignment 2) to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import streamlit as st
import requests
import os
import uuid
from dotenv import load_dotenv
from BD2app.pages import login, signup  # Corrected import path for `pages`


# Load environment variables from .env file
load_dotenv()
# Set the backend URL
backend_url = os.getenv("FASTAPI_BACKEND_URL", "http://127.0.0.1:8000/api/v1")

#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./credentials/damg7245-project2-1daeb31ccdee.json"
# Print to verify environment variables
#print(f"Loaded GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

# Custom CSS Styling (from your previous project)
def add_custom_css():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #000033;
            color: white;
        }
        .stButton button {
            background-color: #1E90FF;
            color: white;
            border-radius: 20px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 10px;
            border: 2px solid #1C6EA4;
            transition: background-color 0.3s, transform 0.3s;
        }
        .stButton button:hover {
            background-color: #4682B4;
            transform: scale(1.05);
        }
        .stTextInput input, .stTextArea textarea {
            background-color: #F0F8FF;
            color: #000;
            border-radius: 12px;
            font-size: 16px;
            padding: 12px;
        }
        h1, h2, h3, h4, h5, h6, p {
            font-family: 'Arial', sans-serif;
        }
        .stApp h1 {
            color: #E0FFFF;
            font-size: 48px;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.4);
        }
        .stApp p {
            font-size: 18px;
            color: #E0FFFF;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# Function to store JWT token after successful login
def store_jwt_in_session(token):
    st.session_state['access_token'] = token

# Function to check if the user is authenticated
def is_authenticated():
    return 'access_token' in st.session_state

# Function to log out and clear the session state
def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_set_query_params(page='login')
    st.success("Successfully logged out. Redirecting to login page...")

# Navigation function to switch between pages
def navigate_to(page):
    st.session_state.page = page
    st.experimental_set_query_params(page=page)

# Main page with user login, and page navigation
def main_page():
    add_custom_css()  # Apply custom CSS for UI consistency

    # Initialize session state for page navigation if not already set
    if 'page' not in st.session_state:
        st.session_state.page = 'login'



    # Page Navigation Logic for Unauthenticated Users (Login and Signup only)
    if not is_authenticated():
        if st.session_state.page == 'login':
            # Show the login page from the `login.py` module
            login.login_page(navigate_to, store_jwt_in_session)

        elif st.session_state.page == 'signup':
            signup.signup_page(navigate_to)  # Call the signup page logic


        else:
            # Redirect unauthenticated users to the login page if they access restricted pages
            navigate_to('login')
            st.warning("Please log in to access the application.")

    # Page Navigation Logic for Authenticated Users (Testing, Validation, Visualization)
    else:
        if st.session_state.page == 'testing':
            from BD2app.pages import testing  # Corrected the import path
            testing.testing_page()  # Call the function from testing.py

        elif st.session_state.page == 'validation':
            from BD2app.pages import validation  # Corrected the import path
            validation.validation_page()  # Call the function from validation.py

        elif st.session_state.page == 'visualization':
            from BD2app.pages import visualization  # Corrected the import path
            visualization.visualization_page()  # Call the function from visualization.py

        else:
            # Redirect authenticated users to the testing page as the default
            navigate_to('testing')
            st.success("You are now logged in. Welcome!")

# Main Entry Point
if __name__ == "__main__":
    main_page()
