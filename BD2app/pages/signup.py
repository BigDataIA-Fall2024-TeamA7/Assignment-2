import streamlit as st
import requests
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
backend_url = os.getenv("FASTAPI_BACKEND_URL")  # Backend URL from .env file

# Basic UI styling
def add_custom_css():
    st.markdown(
        """
        <style>
        .stApp { background-color: #000033; color: white; }
        .stButton button { background-color: #1E90FF; color: white; border-radius: 20px; padding: 12px 24px; font-weight: bold; font-size: 16px; margin-bottom: 10px; border: 2px solid #1C6EA4; transition: background-color 0.3s, transform 0.3s; }
        .stButton button:hover { background-color: #4682B4; transform: scale(1.05); }
        .stTextInput input, .stTextArea textarea { background-color: #F0F8FF; color: #000; border-radius: 12px; font-size: 16px; padding: 12px; }
        .stApp h1 { color: #E0FFFF; font-size: 48px; text-align: center; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.4); }
        .stApp p { font-size: 18px; color: #E0FFFF; }
        </style>
        """,
        unsafe_allow_html=True
    )

# Simple validation functions for input fields
def validate_password(password):
    """Check password strength and validity."""
    errors = []
    if len(password) < 5 or len(password) > 20:
        errors.append("Password must be between 5 and 20 characters long.")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must include at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        errors.append("Password must include at least one lowercase letter.")
    if not re.search(r'[0-9]', password):
        errors.append("Password must include at least one number.")
    return errors

def validate_email(email):
    """Check if email has a valid format."""
    pattern = r"[^@]+@[^@]+\.[^@]+"
    return re.match(pattern, email) is not None

def validate_name(name):
    """Check if the name contains only letters and is at least 2 characters long."""
    return len(name) >= 2 and all(x.isalpha() or x.isspace() for x in name)

# Function to render the signup page UI
def signup_page(navigate_to=None):
    add_custom_css()  # Add custom styling to the page

    st.title("Create a New Account")
    st.subheader("Join us today!")

    # Input fields for user details
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email Address")

    show_password = st.checkbox("Show password")  # Checkbox to toggle password visibility
    password = st.text_input("Password", type="text" if show_password else "password")
    confirm_password = st.text_input("Confirm Password", type="text" if show_password else "password")

    # Button to submit the form
    if st.button("Sign Up"):
        # Validate form inputs
        errors = validate_password(password)
        name_error = not validate_name(first_name) or not validate_name(last_name)

        # Check name validity
        if not validate_name(first_name):
            st.error("First name must contain at least 2 characters and only letters.")
        if not validate_name(last_name):
            st.error("Last name must contain at least 2 characters and only letters.")
        
        # Check if passwords match
        if password != confirm_password:
            st.error("Passwords do not match.")
        # Validate email format
        elif not validate_email(email):
            st.error("Please enter a valid email address.")
        # Show password validation errors
        elif errors:
            st.error("Please fix the following errors:")
            for error in errors:
                st.write(f"- {error}")
        else:
            # Prepare the payload
            payload = {"username": email, "password": password}
            st.write(f"Sending payload: {payload}")  # Print the payload for debugging
            st.write(f"Using backend URL: {backend_url}/register")  # Debugging statement
            # Send a POST request to the backend to create a new user
            response = requests.post(f"{backend_url}/register", json=payload)

            # Check the backend response
            if response.status_code == 200:
                st.success("Your account has been successfully created! You can now log in.")
                if navigate_to:
                    navigate_to('login')  # Navigate to the login page after successful signup
            elif response.status_code == 400:
                st.error("Username already exists. Please choose a different username.")
            else:
                st.error(f"An error occurred during signup. Please try again later. Response: {response.text}")

    # Link to navigate to the login page
    st.markdown("[Go to Login Page](?page=login)")
