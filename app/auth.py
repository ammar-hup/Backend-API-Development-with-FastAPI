import os
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from .models import *
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
ALGORITHM = "HS256"  # Define the algorithm used for JWT

# Secret key for encoding and decoding tokens
# SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")  # Use an environment variableALGORITHM = "HS256"
load_dotenv()  # Load environment variables from .env file
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")  # Set a default for development
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Set the expiration time for access token
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)  # You can set a longer expiration if needed.

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    return user_id