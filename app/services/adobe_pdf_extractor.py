import requests
from app.core.config import settings

def extract_text(file_content: bytes) -> str:
    url = "https://cpf-ue1.adobe.io/ops/:create?respondWith=%7B%22reltype%22%3A%20%22http%3A%2F%2Fns.adobe.com%2Frel%2Fprimary%22%7D"
    headers = {
        "Authorization": f"Bearer {settings.ADOBE_API_KEY}",
        "X-Api-Key": settings.ADOBE_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "contentAnalyzerRequests": [{
            "enable": ["text"],
            "input": {
                "documentDetails": {
                    "content": file_content.decode('latin-1')
                }
            }
        }]
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    # Process the response and extract the text
    result = response.json()
    # we need to parse the result to extract the text based on Adobe's API response structure
    # This is a placeholder and should be adjusted based on the actual response structure
    extracted_text = result.get('text', '')
    
    return extracted_text