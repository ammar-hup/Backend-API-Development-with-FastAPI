from pydantic import BaseModel, EmailStr

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