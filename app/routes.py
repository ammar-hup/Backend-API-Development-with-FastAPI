from fastapi import APIRouter, HTTPException, Depends
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from .models import *
from .schemas import *
from .auth import *
from .database import *

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/users/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    # Check if the user already exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already registered")

    # Hash the password
    hashed_password = pwd_context.hash(user.password)

    # Generate a refresh token (you can set a default, or create a JWT for it)
    refresh_token = create_refresh_token(data={"sub": user.email})  # Create a refresh token based on the user's email

    # Create a new user in the database
    new_user = {
        "name": user.name,
        "email": user.email,
        "hashed_password": hashed_password,
        "refresh_token": refresh_token  # Store the generated refresh token
    }

    result = await users_collection.insert_one(new_user)
    created_user = await users_collection.find_one({"_id": result.inserted_id})  # Fetch the created user

    return user_helper(created_user)  # Ensure user_helper returns the formatted data

@router.post("/users/signin")
async def signin(user: OAuth2PasswordRequestForm = Depends()):
    existing_user = await users_collection.find_one({"email": user.username})
    if existing_user and pwd_context.verify(user.password, existing_user["hashed_password"]):
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(data={"sub": existing_user["email"]}, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data={"sub": existing_user["email"]})

        await users_collection.update_one({"_id": existing_user["_id"]}, {"$set": {"refresh_token": refresh_token}})

        return {
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token  # Ensure you return the refresh token
        }
    
    raise HTTPException(status_code=400, detail="User not found or password incorrect")

@router.post("/refresh-token", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    # Find the user by the provided refresh token
    existing_user = await users_collection.find_one({"refresh_token": request.refresh_token})
    if not existing_user:
        raise HTTPException(status_code=403, detail="Refresh token not found")

    try:
        # Decode the refresh token to get user information
        payload = decode_token(request.refresh_token)
        if payload is None:
            raise HTTPException(status_code=403, detail="Invalid refresh token")

        # Generate a new access token
        new_access_token = create_access_token(data={"sub": payload["sub"]})

        return {
            "message": "Token refreshed successfully",
            "access_token": new_access_token,
            "refresh_token": existing_user["refresh_token"]  # Return the same refresh token
        }
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


