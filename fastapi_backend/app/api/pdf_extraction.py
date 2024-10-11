from fastapi import APIRouter, Depends, File, UploadFile, BackgroundTasks, HTTPException
from app.api.auth import get_current_user
from app.services import adobe_pdf_extractor, opensource_pdf_extractor
from app.core.config import settings
from app.db.bigquery import get_questions
from loguru import logger
from fastapi_cache.decorator import cache

# Initialize router for the API endpoints
router = APIRouter()

# Helper function to get the appropriate PDF extractor (Adobe or OpenSource)
def get_pdf_extractor():
    return adobe_pdf_extractor if settings.USE_ADOBE else opensource_pdf_extractor

# Endpoint to extract PDF content (this endpoint is not used in the main workflow but kept for completeness)
@router.post("/extract-pdf", 
    responses={401: {"description": "Unauthorized"}},
    openapi_extra={
        "security": [{"Bearer Auth": []}]
    }
)
async def extract_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    pdf_extractor = Depends(get_pdf_extractor),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Read the uploaded file contents
        contents = await file.read()
        # Schedule a background task to process the PDF
        background_tasks.add_task(process_pdf, contents, current_user.username, pdf_extractor)
        return {"message": "PDF extraction started"}
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail="PDF extraction failed")

# Function to process the PDF and extract text (used for PDF extraction and analysis)
@cache(expire=3600)
async def process_pdf(contents: bytes, username: str, pdf_extractor):
    try:
        # Extract text using the provided extractor (Adobe or OpenSource)
        text = pdf_extractor.extract_text(contents)
        logger.info(f"PDF processed for user {username}")
        return text
    except Exception as e:
        logger.error(f"PDF processing failed for user {username}: {str(e)}")
        raise

# Endpoint to analyze a PDF using the stored extracted data and AI response generation
@router.post("/analyze-pdf", 
    responses={401: {"description": "Unauthorized"}},
    openapi_extra={
        "security": [{"Bearer Auth": []}]
    }
)
async def analyze_pdf(
    file: UploadFile = File(...),
    pdf_extractor = Depends(get_pdf_extractor),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Read the uploaded file contents
        contents = await file.read()
        # Extract text from the PDF
        extracted_text = await process_pdf(contents, current_user.username, pdf_extractor)

        # Get the questions to be analyzed
        questions = get_questions()
        responses = []

        # Import `get_ai_response` function here to avoid circular import
        from app.services.openai_service import get_ai_response

        # Iterate through questions and generate AI responses
        for question in questions:
            ai_response = get_ai_response(question['text'], extracted_text)
            responses.append({
                "question_id": question['id'],
                "question": question['text'],
                "answer": ai_response
            })
        
        return {"responses": responses}
    except Exception as e:
        logger.error(f"PDF analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="PDF analysis failed")
