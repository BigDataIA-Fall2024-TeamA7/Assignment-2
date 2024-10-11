from google.cloud import bigquery
from app.core.config import settings
from loguru import logger
 
# Initialize BigQuery client
client = bigquery.Client(project=settings.BIGQUERY_PROJECT_ID)
 
def create_users_table_if_not_exists():
    """
    Check if the users table exists.
    If it does not exist, log an error and prevent table creation.
    """
    table_id = f"{settings.BIGQUERY_PROJECT_ID}.{settings.BIGQUERY_DATASET}.users"
 
    try:
        # Attempt to get the table details to check if it exists
        client.get_table(table_id)
        logger.info(f"Table '{table_id}' already exists. No further action needed.")
    except Exception as e:
        # Log an error if the table is missing, but do not attempt to create it
        logger.error(f"Table '{table_id}' does not exist or there is an error accessing it: {str(e)}")
        logger.error("The backend will not attempt to create this table. Please check the table's existence and permissions.")
        return
 
client = bigquery.Client(project=settings.BIGQUERY_PROJECT_ID)
 
def get_questions():
    query = f"""
    SELECT DISTINCT Question, task_id
    FROM `{settings.BIGQUERY_PROJECT_ID}.{settings.BIGQUERY_DATASET}.combinedmetadatatable`
    WHERE ENDS_WITH(file_name, '.pdf')
    ORDER BY Question
    """
   
    try:
        query_job = client.query(query)
        results = list(query_job)
       
        questions = [{"id": row["task_id"], "text": row["Question"]} for row in results]
        return questions
    except Exception as e:
        logger.error(f"Failed to fetch questions: {str(e)}")
        raise
 
 
def get_extracted_data(task_id: str, method: str):
    if method.lower() == "pymupdf":
        query = f"""
        SELECT task_id, pdf_filename, extracted_text, image_count, image_paths
        FROM `{settings.BIGQUERY_PROJECT_ID}.{settings.BIGQUERY_DATASET}.pymuextracted_table`
        WHERE task_id = @task_id
        """
    elif method.lower() == "adobe":
        query = f"""
        SELECT task_id, source, file_path, text
        FROM `{settings.BIGQUERY_PROJECT_ID}.{settings.BIGQUERY_DATASET}.adobe_extracted`
        WHERE task_id = @task_id
        """
    else:
        raise ValueError(f"Unsupported extraction method: {method}")
 
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("task_id", "STRING", task_id),
        ]
    )
   
    try:
        query_job = client.query(query, job_config=job_config)
        results = list(query_job)
        if not results:
            return {"message": "No extracted data found."}
       
        if method.lower() == "pymupdf":
            return {
                "task_id": results[0]["task_id"],
                "pdf_filename": results[0]["pdf_filename"],
                "extracted_text": results[0]["extracted_text"],
                "image_count": results[0]["image_count"],
                "image_paths": results[0]["image_paths"]
            }
        else:  # adobe
            return {
                "task_id": results[0]["task_id"],
                "source": results[0]["source"],
                "file_path": results[0]["file_path"],
                "text": results[0]["text"]
            }
    except Exception as e:
        logger.error(f"Failed to fetch extracted data: {str(e)}")
        raise
 

def get_user(username: str):
    """Fetch user details from the users table based on the username."""
    query = f"""
    SELECT username, hashed_password
    FROM `{settings.BIGQUERY_PROJECT_ID}.{settings.BIGQUERY_DATASET}.users`
    WHERE username = @username
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("username", "STRING", username)
        ]
    )
    try:
        query_job = client.query(query, job_config=job_config)
        results = list(query_job)
        return results[0] if results else None
    except Exception as e:
        logger.error(f"Failed to fetch user {username}: {str(e)}")
        raise
 
def create_user(username: str, hashed_password: str):
    """Create a new user entry in the users table."""
    query = f"""
    INSERT INTO `{settings.BIGQUERY_PROJECT_ID}.{settings.BIGQUERY_DATASET}.users`
    (username, hashed_password)
    VALUES (@username, @hashed_password)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("username", "STRING", username),
            bigquery.ScalarQueryParameter("hashed_password", "STRING", hashed_password)
        ]
    )
    try:
        query_job = client.query(query, job_config=job_config)
        query_job.result()  # Wait for the job to complete
        logger.info(f"User {username} created successfully.")
    except Exception as e:
        logger.error(f"Failed to create user {username}: {str(e)}")
        raise
 
 
 
 
 
 
def create_revoked_tokens_table_if_not_exists():
    query = f"""
    CREATE TABLE IF NOT EXISTS `{settings.BIGQUERY_PROJECT_ID}.{settings.BIGQUERY_DATASET}.revoked_tokens` (
        jti STRING,
        revoked_at TIMESTAMP
    )
    """
 
    try:
 
        job = client.query(query)
 
        job.result()
 
        logger.info("Revoked tokens table created or already exists")
 
    except Exception as e:
 
        logger.error(f"Failed to create revoked tokens table: {str(e)}")
 
def is_token_revoked(jti: str) -> bool:
 
    query = f"""
 
    SELECT COUNT(*) as count
 
    FROM `{settings.BIGQUERY_PROJECT_ID}.{settings.BIGQUERY_DATASET}.revoked_tokens`
 
    WHERE jti = @jti
 
    """
 
    job_config = bigquery.QueryJobConfig(
 
        query_parameters=[
 
            bigquery.ScalarQueryParameter("jti", "STRING", jti)
 
        ]
 
    )
 
    try:
 
        query_job = client.query(query, job_config=job_config)
 
        results = list(query_job)
 
        return results[0]['count'] > 0
 
    except Exception as e:
 
        logger.error(f"Failed to check if token is revoked: {str(e)}")
 
        raise
 
def revoke_token(jti: str):
 
    query = f"""
 
    INSERT INTO `{settings.BIGQUERY_PROJECT_ID}.{settings.BIGQUERY_DATASET}.revoked_tokens`
 
    (jti, revoked_at)
 
    VALUES (@jti, CURRENT_TIMESTAMP())
 
    """
 
    job_config = bigquery.QueryJobConfig(
 
        query_parameters=[
 
            bigquery.ScalarQueryParameter("jti", "STRING", jti)
 
        ]
 
    )
 
    try:
 
        query_job = client.query(query, job_config=job_config)
 
        query_job.result()
 
        logger.info(f"Token {jti} revoked successfully")
 
    except Exception as e:
 
        logger.error(f"Failed to revoke token {jti}: {str(e)}")
 
        raise
 
 