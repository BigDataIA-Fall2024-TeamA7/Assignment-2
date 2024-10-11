from pypdf import PdfReader
import io

def extract_text(file_content: bytes) -> str:
    pdf = PdfReader(io.BytesIO(file_content))
    text = ""
    for page in pdf.pages:
        text += page.extract_text()
    return text