from pydantic import BaseModel

class User(BaseModel):
    username: str
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str