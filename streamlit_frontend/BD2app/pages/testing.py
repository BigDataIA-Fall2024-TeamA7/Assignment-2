import streamlit as st

import requests

from dotenv import load_dotenv

import os

import logging
 
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
 
# Load environment variables from the .env file in the root directory

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
 
# Load environment variables from .env file

backend_url = os.getenv("FASTAPI_BACKEND_URL")  # Backend URL from .env file
 
# Debug print

print(f"Backend URL: {backend_url}")
 
# Custom CSS styling for the page

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
 
# Function to fetch questions from the API

def fetch_questions():

    try:

        response = requests.get(f"{backend_url}/questions", headers=get_auth_headers())

        response.raise_for_status()

        return response.json().get("questions", [])

    except requests.RequestException as e:

        st.error(f"Failed to fetch questions: {str(e)}")

        return []
 
def fetch_extracted_data(task_id, method):

    try:

        # Remove .pdf extension if present

        task_id = task_id.replace('.pdf', '')

        response = requests.get(

            f"{backend_url}/extracted_data",

            params={"task_id": task_id, "method": method},

            headers=get_auth_headers()

        )

        response.raise_for_status()

        data = response.json()

        if method.lower() == "pymupdf":

            return data.get("extracted_text", "No extracted text found.")

        elif method.lower() == "adobe":

            return data.get("text", "No extracted text found.")

        else:

            return "Unsupported extraction method."

    except requests.RequestException as e:

        st.error(f"Failed to fetch extracted data: {str(e)}")

        return "Failed to fetch extracted data."
 
# Function to generate answer

def generate_answer(question, extracted_text):

    try:

        response = requests.post(

            f"{backend_url}/ai-analysis",

            json={"extracted_text": extracted_text},

            headers=get_auth_headers()

        )

        response.raise_for_status()

        ai_responses = response.json().get("responses", [])

        for ai_response in ai_responses:

            if ai_response["question"] == question:

                return ai_response["answer"]

        return "No answer found for the selected question."

    except requests.RequestException as e:

        st.error(f"Failed to generate answer: {str(e)}")

        return "Failed to generate answer."
 
# Helper function to get authentication headers

def get_auth_headers():

    return {"Authorization": f"Bearer {st.session_state.get('access_token', '')}"}
 
# Function to fetch question details

def fetch_question_details(question_id):

    try:

        response = requests.get(

            f"{backend_url}/question/{question_id}",

            headers=get_auth_headers()

        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:

        st.error(f"Failed to fetch question details: {str(e)}")

        return {}
 
# Main function to build the UI of the testing page

def testing_page():

    # Apply custom CSS for styling

    add_custom_css()
 
    # Page Title

    st.title("Test Case Validator")
 
    # Sidebar Guide Section

    with st.sidebar:

        # Guide Section with expandable content

        with st.expander("ℹ️ GUIDE"):

            st.markdown(

                """

                1. **Select a Question**: Choose a question from the dropdown menu.

                2. **Fetch Question Details**: Click to view more information about the selected question.

                3. **Extract Text**: Use PyMuPDF or Adobe to retrieve the stored extracted text.

                4. **Generate an Answer**: Click 'Answer' to generate a response using the LLM.

                5. **Validate Your Answer**: Check if the generated answer matches the expected answer.

                """,

                unsafe_allow_html=True

            )
 
    # Fetch questions from API

    questions = fetch_questions()

    question_texts = ["Select a Question"] + [q["text"] for q in questions]

    # Dropdown for Selecting a Question

    selected_question_text = st.selectbox("Choose a Question:", question_texts)
 
    # If a question is selected, retrieve the corresponding question ID

    if selected_question_text != "Select a Question":

        selected_question_id = next((q["id"] for q in questions if q["text"] == selected_question_text), None)
 
        if selected_question_id:

            st.write(f"Selected Question ID: {selected_question_id}")

 
            # Display Extraction Buttons

            col1, col2 = st.columns(2)
 
            # PyMuPDF Button

            with col1:

                if st.button("PyMuPDF"):

                    with st.spinner("Extracting text using PyMuPDF..."):

                        st.session_state.extraction_method = "PyMuPDF"

                        st.session_state.extracted_text = fetch_extracted_data(selected_question_id, "PyMuPDF")

                    if st.session_state.extracted_text != "Failed to fetch extracted data.":

                        st.success("Text extracted successfully using PyMuPDF.")
 
            # Adobe Button

            with col2:

                if st.button("Adobe"):

                    with st.spinner("Extracting text using Adobe..."):

                        st.session_state.extraction_method = "Adobe"

                        st.session_state.extracted_text = fetch_extracted_data(selected_question_id, "Adobe")

                    if st.session_state.extracted_text != "Failed to fetch extracted data.":

                        st.success("Text extracted successfully using Adobe.")
 
            # Display extracted text

            if "extracted_text" in st.session_state:

                st.text_area("Extracted Data:", value=st.session_state.extracted_text, height=150)

            else:

                st.info("No text extracted yet. Please use PyMuPDF or Adobe extraction.")
 
            # Answer Button to send data to LLM

            if st.button("Answer"):

                if "extracted_text" not in st.session_state or not st.session_state.extracted_text:

                    st.warning("Please extract text data first.")

                else:

                    with st.spinner("Generating answer..."):

                        st.session_state.llm_answer = generate_answer(selected_question_text, st.session_state.extracted_text)

                    st.info("LLM answer generated successfully.")
 
            # Display the generated answer

            if "llm_answer" in st.session_state:

                st.text_area("Generated Answer:", value=st.session_state.llm_answer, height=150)

        else:

            st.error("Failed to retrieve question ID. Please try again.")

    else:

        st.info("Please select a question to proceed.")
 
# Main Entry Point

if __name__ == "__main__":

    testing_page()
 