# Use an official Python runtime as a base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire contents of the project into the container
COPY . .

# Expose the default port for Streamlit
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "BD2app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
