from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str 
class UserLogin(BaseModel):
    name: str
    email: EmailStr
    password: str 