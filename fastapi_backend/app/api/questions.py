from fastapi import APIRouter, Depends, HTTPException
from app.api.auth import get_current_user
from app.db.bigquery import get_questions, get_extracted_data
from app.services.openai_service import get_ai_response
from pydantic import BaseModel
from loguru import logger

router = APIRouter()
 
class AnswerRequest(BaseModel):
    question: str
    extracted_data: str
 
@router.get("/questions")
async def read_questions(current_user: dict = Depends(get_current_user)):
    try:
        questions = get_questions()
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch questions: {str(e)}")
 
 
@router.get("/extracted_data")
async def read_extracted_data(task_id: str, method: str, current_user: dict = Depends(get_current_user)):
    try:
        extracted_data = get_extracted_data(task_id, method)
        return extracted_data
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to fetch extracted data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch extracted data: {str(e)}")
 
 
 
@router.post("/generate_answer")
async def generate_answer(request: AnswerRequest, current_user: dict = Depends(get_current_user)):
    try:
        answer = get_ai_response(request.question, request.extracted_data)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")
