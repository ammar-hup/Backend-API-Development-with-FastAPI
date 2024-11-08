from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserSignin(BaseModel):
    name: str
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str  

class RefreshTokenResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str

class OrganizationMember(BaseModel):
    name: str
    email: EmailStr  # Use EmailStr for validation
    access_level: str
class OrganizationCreate(BaseModel):
    name: str
    description: Optional[str]  # Optional description field

class OrganizationResponse(BaseModel):
    organization_id: str
    name: str
    description: Optional[str]  # Optional description field

class OrganizationUpdate(BaseModel):
    name: Optional[str]  # Optional to allow partial updates
    description: Optional[str]  # Optional to allow partial updates

class DeleteOrganizationResponse(BaseModel):
    message: str

class InviteUserRequest(BaseModel):
    user_email: EmailStr  # User's email to invite

class InviteUserResponse(BaseModel):
    message: str  # Confirmation message