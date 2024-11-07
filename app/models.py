from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: str
    name: str
    email: str
    hashed_password: str
    refresh_token: str = None  

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    refresh_token: Optional[str] = None  # Make it optional if not set