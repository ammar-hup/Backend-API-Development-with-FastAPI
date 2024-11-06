from fastapi import APIRouter, HTTPException
from .models import *
from .schemas import *
from passlib.context import CryptContext  


router = APIRouter()
users = []  

# Set up password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

@router.post("/users/register", response_model=User)
def register_user(user: UserCreate):
    for existing_user in users:
        if existing_user.name == user.name or existing_user.email == user.email:
            raise HTTPException(status_code=400, detail="name or Email already registered")

    # Hash the password and create a new user
    hashed_password = hash_password(user.password)
    new_user = User(id=len(users) + 1, name=user.name, email=user.email, password=hashed_password)
    users.append(new_user)

    return new_user
    ## "user created sucsessfully"


