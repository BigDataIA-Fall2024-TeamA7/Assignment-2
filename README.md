# Automating Text Extraction and Client-Facing Application 

## Live Application Links
- **Streamlit Application**: [Streamlit URL Here](http://your-streamlit-url)

## Problem Statement
Develop an automated text extraction system and a client-facing application that allows users to securely access and query extracted data from PDF files in the GAIA dataset.

## Project Goals
- Automate the acquisition and processing of PDF files from the GAIA dataset.
- Implement a user registration and login system with JWT authentication.
- Provide an interactive interface for users to query and access extracted text data.
- Ensure secure data handling and user authentication throughout the application.

## Technologies Used
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/)
[![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-0A0A0A?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
[![Google Cloud Platform](https://img.shields.io/badge/Google%20Cloud%20Platform-%234285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Airflow](https://img.shields.io/badge/Airflow-17A3B8?style=for-the-badge&logo=apacheairflow&logoColor=white)](https://airflow.apache.org/)
[![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)](https://jwt.io/)
[![BigQuery](https://img.shields.io/badge/BigQuery-0072C6?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/bigquery)

## Pre-requisites
- Knowledge of Python
- Google Cloud Platform account
- Understanding of Streamlit and FastAPI
- Familiarity with JWT authentication
- Experience with Docker

## Architecture Diagram
![Architecture Diagram](https://github.com/BigDataIA-Fall2024-TeamA7/Assignment-2/blob/main/architecture_diagram/architecture_diagram.png)

## Codelab link: [Codelab Document](https://codelabs-preview.appspot.com/?file_id=YOUR_CODELAB_LINK)

## Demo Video
You can view the demo video by clicking [here](https://github.com/SaiPranaviJeedigunta/Assignment-2/blob/main/demo/YOUR_DEMO_VIDEO.mp4).

## How to Run the Application Locally
1. Clone the repository:
   ```bash
   git clone https://github.com/YourUsername/Assignment-2.git
   cd Assignment-2
   ```

2. Navigate to the folder where `requirements.txt` is present:
   ```bash
   cd streamlit_app
   pip install -r requirements.txt
   ```

3. Set up configuration files:
   - Create a `.env` file and add your credentials for GCP and OpenAI API.

4. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

5. Run the FastAPI application:
   ```bash
   uvicorn main:app --reload
   ```

6. Run the Streamlit application:
   ```bash
   streamlit run main.py
   ```

## References
- [GAIA Dataset](https://huggingface.co/datasets/gaia-benchmark/GAIA)
- [Airflow Documentation](https://airflow.apache.org/)
- [OpenAI API](https://openai.com/api/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Cloud Platform](https://cloud.google.com/)

## Team Contributions
| Name                        | Contribution % | Contributions                                      |
|---------------------------  |----------------|----------------------------------------------------|
| Sai Pranavi Jeedigunta      | 33%            | Developed Airflow pipelines for data acquisition   |
| Akanksha Pandey             | 33%            | Implemented FastAPI backend and JWT authentication |
| Kalash Desai                | 33%            | Created Streamlit frontend and integrated services |

---

## **Attestation and Contribution Declaration**:
   > WE ATTEST THAT WE HAVEN’T USED ANY OTHER STUDENTS’ WORK IN OUR ASSIGNMENT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK.
