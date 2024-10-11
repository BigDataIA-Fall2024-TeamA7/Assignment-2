from fastapi import FastAPI, Depends

from fastapi.middleware.cors import CORSMiddleware

from fastapi.openapi.utils import get_openapi

from fastapi_cache import FastAPICache

from fastapi_cache.backends.redis import RedisBackend

from slowapi import Limiter, _rate_limit_exceeded_handler

from slowapi.util import get_remote_address

from slowapi.errors import RateLimitExceeded

from app.api import auth, questions, pdf_extraction, services, ai_analysis

from app.core.config import settings

from app.api.auth import oauth2_scheme

from loguru import logger

import redis

import os

from dotenv import load_dotenv
 
# Load environment variables from .env

load_dotenv()
 
# Initialize Logging

logger.add("app.log", rotation="500 MB")
 
# Setup Rate Limiting

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title=settings.PROJECT_NAME)

app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
 
# Verify if Google Cloud credentials are set correctly

service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
 
# On application startup, initialize Redis cache and verify configurations

@app.on_event("startup")

async def startup_event():

    # Ensure Google Cloud credentials are set correctly

    if not service_account_path or not os.path.isfile(service_account_path):

        logger.error(f"Service account file not found or invalid path: {service_account_path}")

    else:

        logger.info(f"Using Google Cloud credentials at: {service_account_path}")
 
    # Redis Client Setup for caching

    redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
 
# Configure CORS Middleware

app.add_middleware(

    CORSMiddleware,

    allow_origins=settings.ALLOWED_ORIGINS,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)
 
# Customize OpenAPI schema

def custom_openapi():

    if app.openapi_schema:

        return app.openapi_schema

    openapi_schema = get_openapi(

        title=settings.PROJECT_NAME,

        version="1.0.0",

        description="This is a PDF Extraction API",

        routes=app.routes,

    )

    openapi_schema["components"]["securitySchemes"] = {

        "Bearer Auth": {

            "type": "http",

            "scheme": "bearer",

            "bearerFormat": "JWT",

        }

    }

    app.openapi_schema = openapi_schema

    return app.openapi_schema
 
# Set OpenAPI schema customization

app.openapi = custom_openapi
 
# Include all the application routers

app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])

app.include_router(

    questions.router,

    prefix="/api/v1",

    tags=["Questions"],

    dependencies=[Depends(oauth2_scheme)],

    responses={401: {"description": "Unauthorized"}}

)

app.include_router(

    pdf_extraction.router,

    prefix="/api/v1",

    tags=["PDF Extraction"],

    dependencies=[Depends(oauth2_scheme)],

    responses={401: {"description": "Unauthorized"}}

)

app.include_router(

    services.router,

    prefix="/api/v1",

    tags=["Services"],

    dependencies=[Depends(oauth2_scheme)],

    responses={401: {"description": "Unauthorized"}}

)

app.include_router(

    ai_analysis.router,

    prefix="/api/v1",

    tags=["AI Analysis"],

    dependencies=[Depends(oauth2_scheme)],

    responses={401: {"description": "Unauthorized"}}

)
 
# Health Check Endpoint

@app.get("/health")

async def health_check():

    return {"status": "healthy"}
 
# Run the application (for local testing only)

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
 