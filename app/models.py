from pydantic import BaseModel, EmailStr
from typing import Optional,List
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

class Member(BaseModel):
    name: str
    email: str
    access_level: str

class Organization(BaseModel):
    organization_id: str
    name: str
    description: str
    organization_members: List[Member] = []  # Default to an empty list