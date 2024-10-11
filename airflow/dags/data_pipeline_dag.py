from airflow import DAG
from airflow.operators.python_operator import PythonOperator

from google.cloud import storage
from google.oauth2 import service_account
from huggingface_hub import login, list_repo_files, hf_hub_download
from dotenv import load_dotenv
from google.cloud import bigquery
import os
import pandas as pd
import fitz
import logging
import json
import csv
import datetime
from datetime import timedelta
import zipfile
import google.auth
from google.cloud import storage

from glob import glob

from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.exception.exceptions import ServiceApiException, ServiceUsageException, SdkException
from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
from adobe.pdfservices.operation.io.stream_asset import StreamAsset
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import ExtractElementType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.table_structure_type import TableStructureType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_renditions_element_type import ExtractRenditionsElementType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import ExtractPDFParams
from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Also log to a file
file_handler = logging.FileHandler(os.getenv('Error_logs_file', "errors.log"))
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Initialize BigQuery client
client = bigquery.Client(project=os.getenv('PROJECT_ID'))

load_dotenv()

# Define your GCS bucket name
BUCKET_NAME = os.getenv('BUCKET_NAME')
OUTPUT_DIRECTORY = os.getenv('OUTPUT_DIRECTORY')
GCS_EXTRACTED_FOLDER = os.getenv('GCS_EXTRACTED_FOLDER')

# Check for None types in environment variables
if BUCKET_NAME is None:
    logging.error('BUCKET_NAME is not set.')
    exit(1)
if OUTPUT_DIRECTORY is None:
    logging.error('OUTPUT_DIRECTORY is not set.')
    exit(1)
if GCS_EXTRACTED_FOLDER is None:
    logging.error('GCS_EXTRACTED_FOLDER is not set.')
    exit(1)

 # Ensure GCS_CREDENTIALS_PATH is set
# creds_file_path = os.getenv('GCS_CREDENTIALS_PATH')
creds_file_path = google.auth.default()
if not creds_file_path:
    raise ValueError("GCS_CREDENTIALS_PATH environment variable not set.")

# Create credentials using the service account JSON file
# credentials = service_account.Credentials.from_service_account_file(creds_file_path)

# Initialize BigQuery client with the credentials
#client = bigquery.Client(credentials=creds_file_path, project=os.getenv('PROJECT_ID'))
client = bigquery.Client(project=os.getenv('PROJECT_ID'))

# Function to upload Hugging Face files to GCS
def upload_files_to_gcs(hf_repo_id, hf_repo_type, files_to_upload, gcs_bucket_name):
    logger.info("Starting the upload_files_to_gcs function")

    try:
        # Create Google Cloud Storage Client
        # credentials = service_account.Credentials.from_service_account_file(gcs_credentials_path)
        gcs_client = storage.Client()
        bucket = gcs_client.bucket(gcs_bucket_name)

        logger.info("Connected to Google Cloud Storage")

        for file in files_to_upload:
            file_data = hf_hub_download(
                repo_id=hf_repo_id,
                repo_type=hf_repo_type,
                filename=file
            )

            # Upload to GCS
            blob = bucket.blob(file)
            blob.upload_from_filename(file_data)
            logger.info(f"Uploaded {file} to GCS bucket {gcs_bucket_name}")

    except Exception as e:
        logger.error("Failed to upload files to GCS")
        raise e

# Function to list files from Hugging Face repo
def fetch_files_from_huggingface(hf_token, hf_repo_id, hf_repo_type, target_file_path):
    logger.info("huggingface_to_gcs_transfer() - fetch_files_from_huggingface()")
    # Login to Hugging Face
    login(token=hf_token, add_to_git_credential=False)

    # List all files from the Hugging Face repository
    files = list_repo_files(
        repo_id=hf_repo_id,
        repo_type=hf_repo_type
    )

    # Log the files fetched from the repository
    # logger.info(f"Files fetched from Hugging Face repo: {files}")

    # Filter for files in the GAIA folder
    filtered_files = [file for file in files if file.startswith(target_file_path)]
    return filtered_files


# Main function to orchestrate the Hugging Face to GCS transfer
def huggingface_to_gcs_transfer():
    logger.info("huggingface_to_gcs_transfer() - Starting the huggingface_to_gcs_transfer function")

    # Load environment variables from .env file
    load_dotenv()

    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    hf_repo_id = os.getenv("REPO_ID")
    hf_repo_type = os.getenv("REPO_TYPE")
    gcs_bucket_name = os.getenv("BUCKET_NAME")
    gcs_credentials_path = os.getenv("GCS_CREDENTIALS_PATH")
    target_file_path =  os.getenv("FILE_PATH")

    # Fetch the files from Hugging Face
    files_to_upload = fetch_files_from_huggingface(hf_token, hf_repo_id, hf_repo_type, target_file_path)

    # Upload the files to GCS
    upload_files_to_gcs(hf_repo_id, hf_repo_type, files_to_upload, gcs_bucket_name)

# Function to download a single JSON file from GCS
def download_json_file_from_gcs(bucket_name, source_blob_name, destination_file_name):
    logger.info(f"Downloading {source_blob_name} from GCS bucket {bucket_name} to {destination_file_name}")

    # Create GCS client
    # credentials = service_account.Credentials.from_service_account_file(gcs_credentials_path)
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    blob = bucket.blob(source_blob_name)  # Create a blob object for the file
    blob.download_to_filename(destination_file_name)  # Download the file
    logger.info(f"Downloaded {source_blob_name} to {destination_file_name}")

# Function to clean JSON file and save as CSV
def clean_json_file_and_save_as_csv(json_file_path, csv_file_path, dataset_source):
    logger.info(f"Cleaning the file: {json_file_path} and saving as {csv_file_path}")
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            json_lines = json_file.readlines()
        
        cleaned_data = []
        for line in json_lines:
            cleaned_line = line.strip()
            if cleaned_line:  # Only keep non-empty lines
                json_data = json.loads(cleaned_line)
                json_data['dataset_source'] = dataset_source
                cleaned_data.append(json_data)
        
        # Save the cleaned data as a CSV file
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
            if cleaned_data:
                writer = csv.DictWriter(csv_file, fieldnames=cleaned_data[0].keys())
                writer.writeheader()
                writer.writerows(cleaned_data)
                logger.info(f"Cleaned data saved as CSV: {csv_file_path}")
            else:
                logger.warning(f"No valid JSON lines to write to {csv_file_path}")
    except Exception as e:
        logger.error(f"Error processing the file {json_file_path}: {e}")

# Function to upload a file to GCS
def upload_file_to_gcs(bucket_name, local_file_path, destination_blob_name):
    logger.info(f"Uploading {local_file_path} to GCS bucket {bucket_name} as {destination_blob_name}")

    # Create GCS client
    # credentials = service_account.Credentials.from_service_account_file(gcs_credentials_path)
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_file_path)
    logger.info(f"Uploaded {local_file_path} to gs://{bucket_name}/{destination_blob_name}")

# Function to download metadata files
def download_metadata_files():
    load_dotenv()

    gcs_credentials_path = os.getenv("GCS_CREDENTIALS_PATH")
    bucket_name = "gaia_benchmark_data"

    metadata_files = [
        ("2023/test/metadata.jsonl", "metadata_test.jsonl", "metadata_test"),
        ("2023/validation/metadata.jsonl", "metadata_validation.jsonl", "metadata_validation"),
    ]

    # Download each metadata file, clean/save them as CSV, and upload to GCS
    for source_blob_name, destination_file_name, dataset_source in metadata_files:
        download_json_file_from_gcs(bucket_name, source_blob_name, destination_file_name)
        
        csv_file_name = destination_file_name.replace('.jsonl', '.csv')
        clean_json_file_and_save_as_csv(destination_file_name, csv_file_name, dataset_source)

        # Upload the cleaned CSV file back to GCS
        destination_blob_name = f"cleaned_data/{csv_file_name}"  # Define the GCS path
        upload_file_to_gcs(bucket_name, csv_file_name, destination_blob_name)


# Function to validate if a file is a valid PDF
def is_valid_pdf(file_path):
    try:
        with fitz.open(file_path) as pdf:
            return True
    except Exception as e:
        logger.error(f"Invalid PDF file: {file_path}. Error: {e}")
        return False

# Function to download all PDF files from GCS bucket
def download_pdfs_from_gcs(bucket_name, local_directory):
    logger.info("Starting to download PDF files from GCS bucket")

    # Create GCS client
    # credentials = service_account.Credentials.from_service_account_file(gcs_credentials_path)
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Download each PDF file in the bucket
    blobs = bucket.list_blobs()  # List all files in the bucket
    for blob in blobs:
        if blob.name.endswith('.pdf'):  # Check if the file is a PDF
            local_file_path = os.path.join(local_directory, blob.name)
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)  # Create directories if needed
            
            # Download the file
            blob.download_to_filename(local_file_path)
            logger.info(f"Downloaded {blob.name} to {local_file_path}")
            
            # Validate if the file is a valid PDF
            if is_valid_pdf(local_file_path):
                logger.info(f"Validated PDF: {blob.name}")
            else:
                logger.warning(f"Deleting invalid PDF file: {local_file_path}")
                os.remove(local_file_path)

    return local_directory

# Function to extract text and images from a PDF file
def extract_text_and_images_from_pdf(pdf_path):
    logger.info(f"Extracting text and images from {pdf_path}")
    text = ""
    images = []

    try:
        with fitz.open(pdf_path) as pdf_document:
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                text += page.get_text()  # Extract text from the page

                # Extract images from the page
                image_list = page.get_images(full=True)
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    images.append(image_bytes)  # Store images as byte data
                    logger.info(f"Extracted image from {pdf_path}")

        logger.info(f"Extracted text from {pdf_path}, length: {len(text)} characters.")
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
    return text, images

# Function to upload extracted data (text, images, metadata) to GCS
def save_extracted_data_to_gcs(text, pdf_filename, images, metadata, bucket_name):
    logger.info(f"Uploading extracted data for {pdf_filename} to GCS bucket {bucket_name}")

    # Create GCS client
    # credentials = service_account.Credentials.from_service_account_file(gcs_credentials_path)
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    pdf_name_without_extension = os.path.splitext(pdf_filename)[0]

    # Upload images to GCS and update metadata with GCS paths
    metadata['image_paths'] = []
    for img_index, image_bytes in enumerate(images):
        image_filename = f"{pdf_name_without_extension}_img{img_index + 1}.png"
        blob = bucket.blob(f"extracted_data/{pdf_name_without_extension}/{image_filename}")
        blob.upload_from_string(image_bytes, content_type="image/png")
        image_gcs_path = f"gs://{bucket_name}/extracted_data/{pdf_name_without_extension}/{image_filename}"
        logger.info(f"Uploaded image to {image_gcs_path}")
        metadata['image_paths'].append(image_gcs_path)

    # Merge extracted text into the metadata dictionary
    if text:
        metadata['extracted_text'] = text

    # Upload the merged data (text + metadata) as a single JSON to GCS
    json_filename = f"{pdf_name_without_extension}.json"
    blob = bucket.blob(f"extracted_data/{pdf_name_without_extension}/{json_filename}")
    blob.upload_from_string(json.dumps(metadata), content_type="application/json")
    logger.info(f"Uploaded extracted data and metadata to GCS: gs://{bucket_name}/extracted_data/{pdf_name_without_extension}/{json_filename}")

    # Optional: Upload extracted text as CSV to GCS
    if text:
        csv_filename = f"{pdf_name_without_extension}.csv"
        csv_data = f"Extracted Text\n{text}"
        blob = bucket.blob(f"extracted_data/{pdf_name_without_extension}/{csv_filename}")
        blob.upload_from_string(csv_data, content_type="text/csv")
        logger.info(f"Uploaded extracted text as CSV to GCS: gs://{bucket_name}/extracted_data/{pdf_name_without_extension}/{csv_filename}")

def pymuextraction():
    logger.info("Starting main function")

    # Load Environment variables
    load_dotenv()

    bucket_name = os.getenv("BUCKET_NAME")
    gcs_credentials_path = os.getenv("GCS_CREDENTIALS_PATH")
    downloaded_pdfs_directory = "downloaded_pdfs"  # Local directory to temporarily save downloaded PDFs

    # Download PDF files from GCS
    download_directory = download_pdfs_from_gcs(bucket_name, downloaded_pdfs_directory)

    # Extract text and images from each downloaded PDF and upload to GCS
    for root, _, files in os.walk(download_directory):  # Traverse the directory structure
        for pdf_file in files:
            if pdf_file.endswith('.pdf'):
                pdf_path = os.path.join(root, pdf_file)
                logger.info(f"Processing {pdf_path}")  # Log the current PDF being processed
                extracted_text, images = extract_text_and_images_from_pdf(pdf_path)
                
                # Create a metadata dictionary
                metadata = {
                    "pdf_filename": pdf_file,
                    "extracted_text_length": len(extracted_text),
                    "image_count": len(images),
                    "image_paths": []  # This will be filled with paths later
                }
                
                # Save the extracted data directly to GCS
                save_extracted_data_to_gcs(extracted_text, pdf_file, images, metadata, bucket_name)

def get_file_paths(bucket_name,  gcp_folder_path):
    """Retrieve file names from GCS bucket."""
    # credentials = service_account.Credentials.from_service_account_file(gcs_credentials_path)
    storage_client = storage.Client()
    # storage_client = storage.Client.from_service_account_json(creds_file_path)
    blobs = storage_client.list_blobs(bucket_name, prefix=gcp_folder_path)
    file_path_dict = {os.path.basename(blob.name): blob.name for blob in blobs if blob.name.startswith(gcp_folder_path)}
    return file_path_dict

def load_data_into_bigquery(bucket_name):
    """Load data from CSV files in GCS into BigQuery."""
    # Initialize BigQuery client
    client = bigquery.Client(project=os.getenv('PROJECT_ID'))

    # Ensure GCS_CREDENTIALS_PATH is set
    if not creds_file_path:
        raise ValueError("GCS_CREDENTIALS_PATH environment variable not set.")

    # Specify the folder in GCS where the files are located
    gcp_folder_path = "2023/"  # Adjust as needed
    file_paths = get_file_paths(bucket_name, gcp_folder_path)

    # Print the retrieved file paths
    print("File paths retrieved from GCS:")
    for file_name, path in file_paths.items():
        print(f"{file_name}: gs://{bucket_name}/{path}")

    # Load the CSV files from GCS
    test_file_path = os.getenv('TEST_FILE_PATH', 'cleaned_data/metadata_test.csv')
    validation_file_path = os.getenv('VALIDATION_FILE_PATH', 'cleaned_data/metadata_validation.csv')

    test_uri = f'gs://{bucket_name}/{test_file_path}'
    validation_uri = f'gs://{bucket_name}/{validation_file_path}'

    # Load the CSV files
    test_df = pd.read_csv(test_uri)
    validation_df = pd.read_csv(validation_uri)

    # Combine DataFrames
    combined_df = pd.concat([test_df, validation_df], ignore_index=True)

    # Create a column for authenticated file paths or None if not found
    combined_df['file_path'] = combined_df['file_name'].map(
        lambda x: f"https://storage.cloud.google.com/{bucket_name}/{file_paths.get(x)}" if x in file_paths else None
    )

    # If there are no file paths, set all entries in file_path to None
    if not file_paths:
        combined_df['file_path'] = None

    # Ensure task_id is unique
    combined_df['task_id'] = combined_df['file_name']  # Assuming file_name can be used as a unique identifier

    # Define the BigQuery table ID
    table_id = f"{os.getenv('PROJECT_ID')}.{os.getenv('DATASET_ID')}.combinedmetadatatable"

    # Define the schema for the BigQuery table with task_id as a unique identifier
    schema = [
        bigquery.SchemaField("task_id", "STRING"),
        bigquery.SchemaField("Question", "STRING"),
        bigquery.SchemaField("Level", "INTEGER"),
        bigquery.SchemaField("Final answer", "STRING"),
        bigquery.SchemaField("file_name", "STRING"),
        bigquery.SchemaField("Annotator Metadata", "STRING"),
        bigquery.SchemaField("dataset_source", "STRING"),
        bigquery.SchemaField("file_path", "STRING"),  # Renamed to file_path
    ]

    # Define the job configuration
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # Overwrites the table
    )

    # Load the combined DataFrame into BigQuery
    load_job = client.load_table_from_dataframe(combined_df, table_id, job_config=job_config)

    # Wait for the job to complete
    load_job.result()

    # Confirm that the table has been created
    print(f"Loaded {load_job.output_rows} rows into {table_id}.")

def bigquery_load():
    # Load environment variables
    load_dotenv()

    # Get the credentials file path from environment variables
    creds_file_path = google.auth.default()
    # creds_file_path =os.getenv('GCS_CREDENTIALS_PATH')

    # Define your GCS bucket name
    bucket_name = os.getenv('BUCKET_NAME')

    # Load data into BigQuery
    load_data_into_bigquery(bucket_name)

def get_json_file_paths(bucket_name, creds_file_path):
    """Retrieve all JSON file paths from GCS bucket, including subdirectories."""
    storage_client = storage.Client.from_service_account_json(creds_file_path)
    blobs = storage_client.list_blobs(bucket_name, prefix=gcp_folder_path)
    
    json_file_paths = []
    for blob in blobs:
        if blob.name.endswith('.json'):
            json_file_paths.append(f"gs://{bucket_name}/{blob.name}")
            print(f"Found JSON file: {blob.name}")  # Log found JSON files

    return json_file_paths

def clean_text(text):
    """Clean the extracted text to remove unwanted characters."""
    return ' '.join(text.replace("\n", " ").replace("\t", " ").strip().split())

def process_json_files(all_json_files, creds_file_path, bucket_name):
    """Process each JSON file and extract relevant data."""
    data_records = []

    for json_file in all_json_files:
        print(f"Processing JSON file: {json_file}")
        try:
            # Download the raw JSON content
            storage_client = storage.Client.from_service_account_json(creds_file_path)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(json_file.replace(f"gs://{bucket_name}/", ""))
            raw_json = blob.download_as_text()  # Download the raw JSON content
            
            # Load the JSON data from the raw string
            json_data = json.loads(raw_json)

            # Debug: Log the loaded JSON data
            print(f"Loaded JSON data: {json_data}")

            # Check if the JSON data is empty
            if not json_data:
                print(f"No data in JSON file: {json_file}. Skipping.")
                continue

            # Get task_id from the filename (unique identifier)
            task_id = os.path.basename(json_file).split('.')[0]

            # Extracting and cleaning data fields
            extracted_text = json_data.get("extracted_text", '')
            pdf_filename = json_data.get("pdf_filename", '')
            extracted_text_length = json_data.get("extracted_text_length", '')
            image_count = json_data.get("image_count", '')

            # Log extracted fields
            print(f"Extracted text: {extracted_text}, PDF filename: {pdf_filename}, Extracted text length: {extracted_text_length}, Image count: {image_count}")

            # Create a data record from the JSON data
            data_record = {
                "task_id": task_id,
                "pdf_filename": pdf_filename,
                "extracted_text_length": extracted_text_length,
                "image_count": image_count,
                "extracted_text": clean_text(extracted_text),
                "image_paths": json.dumps(json_data.get("image_paths", [])),
            }

            # Check if data_record contains valid data before appending
            if any(value is not None and value != '' for value in data_record.values()):
                data_records.append(data_record)
            else:
                print(f"No valid data found in record for {json_file}. Skipping.")

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {json_file}: {e}")
        except Exception as e:
            print(f"Error reading {json_file}: {e}")

    return data_records

def filter_invalid_records(data_records):
    """Filter out records where task_id is present but critical columns (except image_count) are null or empty."""
    filtered_records = []

    for record in data_records:
        # Check if the essential fields have non-empty, valid values, but allow image_count to be null
        if (
            record.get("pdf_filename") and
            record.get("extracted_text_length") and
            record.get("extracted_text")  # Ensure extracted_text is not empty
        ):
            filtered_records.append(record)  # Only append if all conditions (except image_count) are satisfied
        else:
            print(f"Skipping task_id {record.get('task_id')} due to missing or empty values in critical fields.")
    
    return filtered_records

def load_data_to_bigquery(data_records):
    """Load the extracted data into BigQuery."""
    client = bigquery.Client(project=os.getenv('PROJECT_ID'))
    pymuextracted_table_id = f"{os.getenv('PROJECT_ID')}.{os.getenv('DATASET_ID')}.pymuextracted_table"
    
    # Convert to DataFrame
    data_df = pd.DataFrame(data_records)

    # Check if data_df is empty
    if data_df.empty:
        print("No data to load into BigQuery.")
        return

    # Log the shape of the DataFrame before loading
    print(f"DataFrame shape before filtering: {data_df.shape}")

    # Filter out rows with task_id 'test'
    data_df = data_df[data_df['task_id'] != 'test']

    # Log the shape after filtering
    print(f"DataFrame shape after filtering: {data_df.shape}")

    # Define the schema for the BigQuery table
    schema = [
        bigquery.SchemaField("task_id", "STRING"),
        bigquery.SchemaField("pdf_filename", "STRING"),
        bigquery.SchemaField("extracted_text_length", "INTEGER"),
        bigquery.SchemaField("image_count", "INTEGER"),
        bigquery.SchemaField("image_paths", "STRING"),
        bigquery.SchemaField("extracted_text", "STRING"),
    ]

    # Define the job configuration
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    # Load the DataFrame into BigQuery
    load_job = client.load_table_from_dataframe(data_df, pymuextracted_table_id, job_config=job_config)

    # Wait for the job to complete
    load_job.result()

    # Confirm that the table has been created
    print(f"Loaded {load_job.output_rows} rows into {pymuextracted_table_id}.")

def bigqueryextractedload():
    # Initialize variables
    bucket_name = os.getenv('BUCKET_NAME')
    creds_file_path = os.getenv('GCS_CREDENTIALS_PATH')

    # Specify the folder in GCS where the JSON files are located
    gcp_folder_path = "extracted_data/"  # This should cover all subfolders
    all_json_files = get_json_file_paths(bucket_name, creds_file_path)

    # Log the total number of JSON files found
    print(f"Found {len(all_json_files)} JSON files.")

    # Process the JSON files and extract relevant data
    if all_json_files:
        data_records = process_json_files(all_json_files, creds_file_path, bucket_name)

        # Load the extracted data into BigQuery
        load_data_to_bigquery(data_records)
    else:
        print("No JSON files found to process.")

class ExtractTextInfoFromPDF:
    logger.info("adobeextract() - ExtractTextInfoFromPDF()")
    def __init__(self, pdf_files):
        self.pdf_files = pdf_files
        output_dir = os.path.join(os.getcwd(), os.getenv("OUTPUT_DIRECTORY"))
        if output_dir is None:
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created directory: {output_dir}")
        self.output_folder = os.path.join(os.getcwd(), output_dir)
        self.process_files()

    def process_files(self):
        for pdf_file in self.pdf_files:
            self.current_pdf_file = pdf_file  # Track the current PDF file
            zip_file = self.create_zip_file_path(pdf_file)
            try:
                with open(pdf_file, 'rb') as file:
                    input_stream = file.read()

                with open('Adobe_Credentials.json', 'r') as file:
                    credentials = json.load(file)

                # Initial setup, create credentials instance
                credentials = ServicePrincipalCredentials(
                    client_id=credentials['CLIENT_ID'],
                    client_secret=credentials['CLIENT_SECRETS'][0]
                )

                # Creates a PDF Services instance
                pdf_services = PDFServices(credentials=credentials)

                # Creates an asset from the source file and upload
                input_asset = pdf_services.upload(input_stream=input_stream, mime_type=PDFServicesMediaType.PDF)

                # Create parameters for the job
                extract_pdf_params = ExtractPDFParams(
                    elements_to_extract=[ExtractElementType.TEXT, ExtractElementType.TABLES],
                    elements_to_extract_renditions=[ExtractRenditionsElementType.FIGURES],
                    table_structure_type=TableStructureType.CSV
                )

                # Creates a new job instance
                extract_pdf_job = ExtractPDFJob(input_asset=input_asset, extract_pdf_params=extract_pdf_params)

                # Submit the job and get the job result
                location = pdf_services.submit(extract_pdf_job)
                pdf_services_response = pdf_services.get_job_result(location, ExtractPDFResult)

                # Get content from the resulting asset
                result_asset: CloudAsset = pdf_services_response.get_result().get_resource()
                stream_asset: StreamAsset = pdf_services.get_content(result_asset)

                # Save the ZIP file and unzip it
                self.save_and_unzip_file(stream_asset, zip_file)

            except (ServiceApiException, ServiceUsageException, SdkException) as e:
                logger.error(f'Exception encountered while executing operation on {pdf_file}: {e}')

    def create_zip_file_path(self, pdf_file) -> str:
        return f"{self.output_folder}/extract_{os.path.basename(pdf_file).replace('.pdf', '')}.zip"
    
    def save_and_unzip_file(self, stream_asset, zip_file_name):
        # Create the adobe_outputs directory if it doesn't exist
        output_dir = os.path.join(os.getcwd(), 'adobe_outputs')
        os.makedirs(output_dir, exist_ok=True)

        # Construct the path for the ZIP file in the adobe_outputs directory
        zip_file_path = os.path.join(output_dir, zip_file_name)

        # Save ZIP file to disk in the adobe_outputs directory
        with open(zip_file_path, "wb") as zip_output:
            zip_output.write(stream_asset.get_input_stream())

        # Unzip all files into the output folder
        with zipfile.ZipFile(zip_file_path, 'r') as archive:
            archive.extractall(self.output_folder)
            logger.info(f"Extracted files from {zip_file_path} into {self.output_folder}")

        # Process the extracted files
        self.process_json_from_unzipped_folder()

    def process_json_from_unzipped_folder(self):
        # Process the JSON file inside the unzipped folder
        json_file_path = os.path.join(self.output_folder, 'structuredData.json')
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as json_file:
                data = json.load(json_file)

                # Print or process extracted data from JSON
                for element in data.get("elements", []):
                    if element["Path"].endswith("/H1"):
                        logger.info(f"Text from {self.current_pdf_file}: {element['Text']}")  # Use self.current_pdf_file
        else:
            logger.error(f"No structuredData.json found in {self.output_folder}")

def adobeextract():
    # Define the paths to your PDF files
    pdf_paths = []
    pdf_paths.append(os.path.join(os.getcwd(), "downloaded_pdfs", '2023', 'test', '*.pdf'))  # Added '*.pdf' to match PDF files
    pdf_paths.append(os.path.join(os.getcwd(), "downloaded_pdfs", '2023', 'validation', '*.pdf'))  # Added '*.pdf' to match PDF files)
    
    # Collect all PDF files from the specified directories
    pdf_files = []
    for path in pdf_paths:
        pdf_files.extend(glob(path))

    # Check if any PDF files were found
    if pdf_files:
        # Create an instance of the class with the collected PDF files
        extractor = ExtractTextInfoFromPDF(pdf_files)
    else:
        logger.error("No PDF files found in the specified directories.")

def unzip_and_upload_to_gcs(zip_file_path, bucket_name, gcs_extracted_folder):
    # Create a local directory to unzip files named after the zip file
    zip_file_name = os.path.splitext(os.path.basename(zip_file_path))[0]
    local_extract_dir = os.path.join(os.getcwd(), GCS_EXTRACTED_FOLDER, zip_file_name)
    os.makedirs(local_extract_dir, exist_ok=True)

    logging.info(f'Unzipping {zip_file_path} to {local_extract_dir}')  # Check extraction path
    

    # Unzip the file into its respective folder
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(local_extract_dir)

    logging.info(f'Files extracted: {os.listdir(local_extract_dir)}')  # List extracted files

    # Initialize Google Cloud Storage client
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Upload extracted files to GCS in their respective folders
    for root, dirs, files in os.walk(local_extract_dir):
        for file in files:
            local_file_path = os.path.join(root, file)

            # Extract the base name of the PDF from the zip file name for folder creation
            pdf_base_name = zip_file_name  # Assuming each zip file corresponds to one PDF

            # Construct a GCS file path using the PDF base name as a folder, and prefix the file name with the PDF name
            prefixed_file_name = f"{pdf_base_name}_{file}"  # Prefix the original file name with the PDF base name
            gcs_file_path = os.path.join(gcs_extracted_folder, pdf_base_name, prefixed_file_name)

            # Print before upload
            logging.info(f'Preparing to upload {local_file_path} to gs://{bucket_name}/{gcs_file_path}')
            
            # Upload the file with error handling
            try:
                blob = bucket.blob(gcs_file_path)
                blob.upload_from_filename(local_file_path)
                logging.info(f'Uploaded {local_file_path} to gs://{bucket_name}/{gcs_file_path}')  # Check upload path
            except Exception as e:
                logging.error(f'Error uploading {local_file_path} to gs://{bucket_name}/{gcs_file_path}: {e}')

def adobetogcs():
    # Check if the output directory exists
    output_dir = os.path.join(os.getcwd(), os.getenv("OUTPUT_DIRECTORY"))
    if not os.path.exists(output_dir):
        logging.error(f'Output directory {output_dir} does not exist.')
        exit(1)

    # Loop through all zip files in the output directory
    for zip_file in os.listdir(output_dir):
        if zip_file.endswith('.zip'):
            zip_file_path = os.path.join(output_dir, zip_file)
            unzip_and_upload_to_gcs(zip_file_path, BUCKET_NAME, GCS_EXTRACTED_FOLDER)

def get_json_file_paths(bucket_name,  gcp_folder_path):
    """Retrieve JSON file paths from GCS bucket."""
    # storage_client = storage.Client.from_service_account_json(creds_file_path)
    storage_client = storage.Client()
    blobs = list(storage_client.list_blobs(bucket_name, prefix=gcp_folder_path))

    # Debug: List all blobs found
    print("Listing blobs in GCS bucket:")
    for blob in blobs:
        print(blob.name)

    # Filter for JSON files that match the expected naming pattern
    json_file_paths = [
        f"gs://{bucket_name}/{blob.name}" 
        for blob in blobs 
        if blob.name.endswith('_structuredData.json')
    ]
    return json_file_paths

def process_json_files1(all_json_files):
    """Process each JSON file and extract relevant data."""
    data_records = []

    for json_file in all_json_files:
        print(f"Processing JSON file: {json_file}")
        try:
            # Download the raw JSON content
            # storage_client = storage.Client.from_service_account_json(os.getenv('GCS_CREDENTIALS_PATH'))
            storage_client = storage.Client()
            bucket = storage_client.bucket(os.getenv('BUCKET_NAME'))
            blob = bucket.blob(json_file.replace(f"gs://{os.getenv('BUCKET_NAME')}/", ""))
            raw_json = blob.download_as_text()

            # Load the JSON data from the raw string
            json_data = json.loads(raw_json)

            if not json_data:
                print(f"No data in JSON file: {json_file}. Skipping.")
                continue

            # Extract the source and PDF name from the folder name
            source = os.path.basename(os.path.dirname(json_file))
            pdf_name = source.split('_')[1]  # Extract the PDF name from the folder name

            # Combine all text from elements into one string
            combined_text = " ".join([element.get('Text', '') for element in json_data.get('elements', [])])

            # Create a data record with the renamed fields
            data_record = {
                "task_id": pdf_name,  # Set pdf_name as task_id
                "source": source,      # Set task_id as source
                "file_path": json_file,
                "text": combined_text  # All text combined into one column
            }
            data_records.append(data_record)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {json_file}: {e}")
        except Exception as e:
            print(f"Error reading {json_file}: {e}")

    print(f"Total records to insert: {len(data_records)}")  # Debugging line
    return data_records

def load_data_to_bigquery(data_records):
    """Load the extracted data into BigQuery."""
    client = bigquery.Client(project=os.getenv('PROJECT_ID'))
    pymuextracted_table_id = f"{os.getenv('PROJECT_ID')}.{os.getenv('DATASET_ID')}.adobe_extracted"

    data_df = pd.DataFrame(data_records)

    if data_df.empty:
        print("No data to load into BigQuery.")
        return

    schema = [
        bigquery.SchemaField("task_id", "STRING"),  # PDF name as task_id
        bigquery.SchemaField("source", "STRING"),    # Original task_id as source
        bigquery.SchemaField("file_path", "STRING"),
        bigquery.SchemaField("text", "STRING"),      # Schema for the extracted text
    ]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    load_job = client.load_table_from_dataframe(data_df, pymuextracted_table_id, job_config=job_config)
    load_job.result()

    print(f"Loaded {load_job.output_rows} rows into {pymuextracted_table_id}.")

def adobe_table():
    bucket_name = os.getenv('BUCKET_NAME')
    # creds_file_path = os.getenv('GCS_CREDENTIALS_PATH')
    creds_file_path = google.auth.default()

    gcp_folder_path = os.getenv('GCS_EXTRACTED_FOLDER', 'adobe_extracted/')
    
    all_json_files = get_json_file_paths(bucket_name,  gcp_folder_path)

    print(f"Found {len(all_json_files)} JSON files.")

    data_records = process_json_files1(all_json_files)

    load_data_to_bigquery(data_records)

def create_users_table():
    """Create a users table in BigQuery if it doesn't exist."""
    client = bigquery.Client(project=os.getenv('PROJECT_ID'))
    
    table_id = f"{os.getenv('PROJECT_ID')}.{os.getenv('DATASET_ID')}.users"
    
    schema = [
        bigquery.SchemaField("username", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("email", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("hashed_password", "STRING", mode="REQUIRED"),
    ]

    table = bigquery.Table(table_id, schema=schema)

    try:
        # Create the table if it doesn't exist
        table = client.create_table(table)
        print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"Table {table_id} already exists.")
        else:
            print(f"Error creating table {table_id}: {e}")

def users_table():
    create_users_table()



# Define the default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime.datetime(2023, 10, 1),
}

# Define the DAG
with DAG(
    'data_pipeline_dag',
    default_args=default_args,
    description='A DAG to transfer files from Hugging Face to GCS, clean metadata, extract data using pymupdf and adobe extract, and load into BigQuery.',
    schedule_interval='@daily',  # Change as needed
) as dag:

    # Task to transfer files from Hugging Face to GCS
    transfer_task = PythonOperator(
        task_id='huggingface_to_gcs_transfer',
        python_callable=huggingface_to_gcs_transfer,
        provide_context=True,
    )

    # Task to download metadata files
    download_metadata_task = PythonOperator(
        task_id='download_metadata_files',
        python_callable=download_metadata_files,
        provide_context=True,
    )

    # Task for the main extraction process
    extraction_task = PythonOperator(
        task_id='pymuextraction',
        python_callable=pymuextraction,
        provide_context=True,
    )

    # Task to load data into BigQuery
    load_data_task = PythonOperator(
        task_id='bigquery_load',
        python_callable=bigquery_load,
        provide_context=True,
    )

    # Task to unzip and upload extracted files to GCS
    BigQueryload_task = PythonOperator(
        task_id='bigqueryextractedload',
        python_callable=bigqueryextractedload,
        provide_context=True,
    )
    # Task for adobe extract
    adobe_extract_task = PythonOperator(
        task_id='adobeextract',
        python_callable=adobeextract,
        provide_context=True,
    )
    # Task for adobe extracted data save to gcp
    adobe_save_task = PythonOperator(
        task_id='adobetogcs',
        python_callable=adobetogcs,
        provide_context=True,
    )
    # Task for adobe extracted data from gcp to table
    adobe_bigquery_table = PythonOperator(
        task_id='adobe_table',
        python_callable=adobe_table,
        provide_context=True,
    )
    # Task for creating userstable
    users_table_task = PythonOperator(
        task_id='users_table',
        python_callable=users_table,
        provide_context=True,
    )


    # Setting task dependencies
    transfer_task >> download_metadata_task >> extraction_task >> load_data_task >> BigQueryload_task >> adobe_extract_task >> adobe_save_task >> adobe_bigquery_table >> users_table_task

