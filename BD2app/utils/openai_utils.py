import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI API Key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_openai_response(prompt, model="gpt-4"):
    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()
