import openai
from app.core.config import settings
 
openai.api_key = settings.OPENAI_API_KEY
 
def get_ai_response(question: str, extracted_text: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                {"role": "user", "content": f"Context: {extracted_text}\n\nQuestion: {question}"}
            ],
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        raise Exception(f"Error in OpenAI API call: {str(e)}")
