FROM python:3.9

WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app ./app

# Copy the credentials file
COPY ./credentials/damg7245-project2-1daeb31ccdee.json ./credentials/damg7245-project2-1daeb31ccdee.json

# Set the environment variable for Google Cloud credentials
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/damg7245-project2-1daeb31ccdee.json

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]