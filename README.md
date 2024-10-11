# Automating Text Extraction and Client-Facing Application 

## Live Application Links
- **Streamlit Application**: [Streamlit URL Here](http://your-streamlit-url)

## Problem Statement
Develop an automated text extraction system and a client-facing application that allows users to securely access and query extracted data from PDF files in the GAIA dataset.

## Project Summary
The Automated Text Extraction Application leverages advanced techniques to extract and analyze textual data from a variety of document formats, converting unstructured data into actionable insights. This client-facing application features a user-friendly interface built with Streamlit, a robust backend powered by FastAPI, and an automated extraction pipeline managed by Apache Airflow. The integration of Google Cloud technologies and the OpenAI API enhances its capabilities, making it a valuable tool for organizations seeking to improve their decision-making processes.

## Research Background
In a rapidly evolving digital landscape, organizations increasingly rely on data to inform their strategies and operations. Unstructured data, such as text from PDFs, emails, and documents, often holds critical information that can drive business insights. Research shows that automating text extraction and analysis significantly improves operational efficiency, enabling teams to focus on high-value tasks rather than manual data processing. This project draws upon current methodologies and tools in the field of text extraction, natural language processing, and cloud computing to develop a scalable solution.

## Proof of Concept (PoC)
The proof of concept demonstrates the core functionalities of the application, showcasing its ability to:

Extract text from PDF and other document formats using both open-source (PyMuPDF) and proprietary (Adobe API) tools.
Store and manage extracted data in Google Cloud Storage, utilizing Google BigQuery for efficient data retrieval and analysis.
Process natural language queries through the OpenAI API, providing users with relevant insights based on their inquiries.
Automate the workflow using Apache Airflow, ensuring reliable task scheduling and monitoring.
The PoC has been tested with various document formats, yielding positive results in terms of extraction accuracy and response times.

## Project Goals
The Automated Text Extraction Application aims to transform unstructured text data into actionable insights through the following key objectives:

1. Automated Text Extraction: Implement a pipeline that extracts text from various document formats with high accuracy and efficiency.

2. User-Centric Interface: Create an intuitive interface using Streamlit, enabling users to submit queries and receive organized results seamlessly.

3. Efficient Data Storage: Utilize Google Cloud Storage (GCS) for secure text data storage and Google BigQuery for fast data analysis.

4. Natural Language Querying: Integrate the OpenAI API for intelligent query processing, allowing users to ask complex questions and receive relevant responses.

5. Workflow Automation: Use Apache Airflow to automate the extraction pipeline, ensuring efficient task scheduling and monitoring.

6. Consistent Deployment: Containerize the application with Docker for consistent deployment across different environments.

7. Scalability: Design the application to handle varying workloads, ensuring scalability and flexibility for future enhancements.

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

## Codelab link: [Codelab Document](https://codelabs-preview.appspot.com/?file_id=https://docs.google.com/document/d/12JeDAVi8MTSUe7OpSaZXqRY3w_g-el0ALN3J2ZGNFZI/edit?tab=t.0#0)

## Demo Video
You can view the demo video by clicking [here](https://github.com/SaiPranaviJeedigunta/Assignment-2/blob/main/demo/YOUR_DEMO_VIDEO.mp4).

# PDF Extraction Evaluation Template

You can find the PDF extraction evaluation template [here](https://github.com/BigDataIA-Fall2024-TeamA7/Assignment-2/blob/main/pdf_extraction_evalutaion/PDF_Extraction_API_Evaluation_Template_.pdf).

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
