FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

# Copy the credentials file
COPY ./credentials/damg7245-project2-1daeb31ccdee.json /credentials/

ENV GOOGLE_APPLICATION_CREDENTIALS=/credentials/damg7245-project2-1daeb31ccdee.json

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]