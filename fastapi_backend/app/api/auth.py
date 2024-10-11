
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.db.bigquery import get_user, create_user
from app.schemas.user import UserCreate, Token, UserInDB
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.db.bigquery import revoke_token, is_token_revoked

# Initialize FastAPI router and limiter
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# OAuth2 scheme for dependency injection in endpoints
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Helper function to retrieve the current user from the token
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception
    return UserInDB(**user)

# Registration endpoint for new users
@router.post("/register", response_model=Token)
@limiter.limit("5/minute")
def register(request: Request, user: UserCreate):
    try:
        # Check if the user already exists
        logger.info(f"Registering new user: {user.username}")
        db_user = get_user(user.username)
        if db_user:
            logger.warning(f"Registration failed: Username {user.username} already registered.")
            raise HTTPException(status_code=400, detail="Username already registered")

        # Hash the password and store the user in the database
        hashed_password = get_password_hash(user.password)
        create_user(user.username, hashed_password)
        logger.info(f"User {user.username} successfully registered.")

        # Generate an access token for the newly registered user
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Registration failed for user {user.username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Login endpoint to authenticate users and issue JWT tokens


@router.post("/token", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # Debugging step: log the username trying to log in
        print(f"Login attempt with username: {form_data.username}")

        # Retrieve the user from the database
        user = get_user(form_data.username)
        print(f"User fetched from DB: {user}")  # Debug fetched user details

        # Check if user exists and if password matches
        if not user:
            print(f"User not found: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify if the entered password matches the stored hashed password
        if not verify_password(form_data.password, user["hashed_password"]):
            print(f"Password mismatch for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Log successful login before generating the access token
        print(f"Successful login for user: {form_data.username}")

        # Generate an access token for the authenticated user
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"]}, expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        # Log detailed exception error for 500 Internal Server Error debugging
        print(f"Login failed for user {form_data.username}: {str(e)}")
        logger.error(f"Login failed for user {form_data.username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")



@router.post("/refresh-token", response_model=Token)

async def refresh_token(current_token: str = Depends(oauth2_scheme)):

    try:

        payload = jwt.decode(current_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        username: str = payload.get("sub")

        if username is None:

            raise HTTPException(status_code=401, detail="Invalid token")

        user = get_user(username)

        if user is None:

            raise HTTPException(status_code=401, detail="User not found")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        new_token = create_access_token(

            data={"sub": username}, expires_delta=access_token_expires

        )

        return {"access_token": new_token, "token_type": "bearer"}

    except JWTError:

        raise HTTPException(status_code=401, detail="Invalid token")



@router.post("/revoke-token")
async def revoke_token(current_token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(current_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        jti = payload.get("jti")
        if jti is None:
            raise HTTPException(status_code=400, detail="Invalid token")
        revoke_token(jti)
        return {"message": "Token revoked successfully"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
 