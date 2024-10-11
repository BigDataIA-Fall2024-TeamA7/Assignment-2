import streamlit as st
import requests
import os
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
backend_url = os.getenv("FASTAPI_BACKEND_URL")  # Backend URL from .env file

def login_page(navigate_to, store_jwt_in_session):
    st.title("Login to the Application")  # Page Title
    st.subheader("Please enter your login credentials")

    # Create input fields for email and password
    email = st.text_input("Email Address", placeholder="Enter your email")
    password = st.text_input("Password", type="password", placeholder="Enter your password")

    # Placeholder area for displaying messages
    message_area = st.empty()

    # Login Button
    if st.button("Login"):
        # Check if both email and password are provided
        if email and password:
            try:
                # Send a POST request to the backend's /token endpoint
                response = requests.post(
                    f"{backend_url}/token",
                    data={"username": email, "password": password}
                )

                # Check the response status
                if response.status_code == 200:
                    # If login is successful, store the JWT token in session state
                    jwt_token = response.json().get("access_token")
                    store_jwt_in_session(jwt_token)  # Store the actual JWT token

                    # Generate a unique session ID for analytics purposes
                    session_id = str(uuid.uuid4())  # Generate a unique session ID
                    st.session_state['user_email'] = email
                    st.session_state['session_id'] = session_id  # Store the session ID in the state

                    # Display success message and navigate to the testing page
                    st.success(f"Welcome back, {email}!")
                    navigate_to('testing')  # Redirect to testing page after login

                    # Log the analytics event
                    st.info(f"Analytics: Session ID {session_id} created for user {email}.")
                elif response.status_code == 401:
                    # 401 indicates Unauthorized - likely incorrect username or password
                    message_area.error("Incorrect email or password. Please try again.")
                else:
                    # Other errors (e.g., 500)
                    message_area.error(f"Server error: {response.status_code}. Please try again later.")
            except requests.exceptions.RequestException as e:
                # Handle request errors (e.g., network issues)
                message_area.error(f"An error occurred: {e}")
        else:
            # Display a message if either email or password is missing
            message_area.warning("Please enter both email and password.")

    # Sign-Up Button (Redirect to the signup page)
    if st.button("Sign Up"):
        navigate_to('signup')
