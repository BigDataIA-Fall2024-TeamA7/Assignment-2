from fastapi import APIRouter, Depends, HTTPException

from app.services.openai_service import get_ai_response

from app.api.auth import get_current_user

from app.db.bigquery import get_questions

from pydantic import BaseModel

from typing import List
 
router = APIRouter()
 
class AIAnalysisRequest(BaseModel):

    extracted_text: str
 
class AIResponse(BaseModel):

    question_id: str

    question: str

    answer: str
 
class AIAnalysisResponse(BaseModel):

    responses: List[AIResponse]
 
@router.post("/ai-analysis", response_model=AIAnalysisResponse,

    responses={

        401: {"description": "Unauthorized"},

        500: {"description": "Internal server error"}

    },

    openapi_extra={

        "security": [{"Bearer Auth": []}]

    }

)

async def analyze_text(

    request: AIAnalysisRequest,

    current_user: dict = Depends(get_current_user)

):

    try:

        questions = get_questions()

        responses = []

        for question in questions:

            ai_response = get_ai_response(question['text'], request.extracted_text)

            responses.append(AIResponse(

                question_id=question['id'],

                question=question['text'],

                answer=ai_response

            ))
        return AIAnalysisResponse(responses=responses)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
 