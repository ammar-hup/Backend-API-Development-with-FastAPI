from fastapi import APIRouter, HTTPException, Depends
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from .models import *
from .schemas import *
from .auth import *
from .database import *
from bson import ObjectId
from typing import List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

@router.post("/organization", response_model=OrganizationResponse)
async def create_organization(org: OrganizationCreate, token: str = Depends(oauth2_scheme)):
    # Prepare the new organization document
    new_organization = {
        "name": org.name,
        "description": org.description,  # Add description
    }

    # Insert the new organization into the database
    result = await organizations_collection.insert_one(new_organization)

    # Return the response with the generated organization ID and other details
    return OrganizationResponse(
        organization_id=str(result.inserted_id),  # Generate ID here
        name=org.name,
        description=org.description
    )

@router.get("/organization/{organization_id}", response_model=OrganizationResponse)
async def read_organization(organization_id: str, token: str = Depends(oauth2_scheme)):
    user_id = get_current_user(token)  # Ensure user is authenticated

    # Find the organization in the database
    organization = await organizations_collection.find_one({"_id": ObjectId(organization_id)})
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Fetch members from the organization document (assuming they are stored correctly)
    organization_members = [
        OrganizationMember(name=member["name"], email=member["email"], access_level=member["access_level"])
        for member in organization.get("members", [])  # Adjust based on your actual data structure
    ]

    # Construct and return the response using OrganizationResponse schema
    return OrganizationResponse(
        organization_id=str(organization["_id"]),
        name=organization["name"],
        description=organization["description"],
        organization_members=organization_members,
    )


@router.get("/organizations", response_model=List[OrganizationResponse])
async def read_all_organizations(token: str = Depends(oauth2_scheme)):
    user_id = get_current_user(token)  # Ensure user is authenticated

    organizations = []
    
    async for organization in organizations_collection.find():
        organization_members = [
            OrganizationMember(name=member["name"], email=member["email"], access_level=member["access_level"])
            for member in organization.get("members", [])  # Adjust based on your actual data structure
        ]
        
        organizations.append(OrganizationResponse(
            organization_id=str(organization["_id"]),
            name=organization["name"],
            description=organization["description"],
            organization_members=organization_members,
        ))

    return organizations  # This will return a list of OrganizationResponse objects

@router.put("/organization/{organization_id}", response_model=OrganizationResponse)
async def update_organization(organization_id: str, org: OrganizationUpdate, token: str = Depends(oauth2_scheme)):
    # Find the organization in the database
    organization = await organizations_collection.find_one({"_id": ObjectId(organization_id)})

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Prepare the update fields. Only update fields that are provided in the request.
    update_data = {}
    if org.name:
        update_data["name"] = org.name
    if org.description:
        update_data["description"] = org.description

    # Update the organization in the database
    result = await organizations_collection.update_one(
        {"_id": ObjectId(organization_id)},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Update failed, no changes made")

    # Return the updated organization details
    updated_organization = await organizations_collection.find_one({"_id": ObjectId(organization_id)})
    return OrganizationResponse(
        organization_id=str(updated_organization["_id"]),
        name=updated_organization["name"],
        description=updated_organization["description"]
    )

@router.delete("/organization/{organization_id}", response_model=DeleteOrganizationResponse)
async def delete_organization(organization_id: str, token: str = Depends(oauth2_scheme)):
    # Find the organization in the database
    organization = await organizations_collection.find_one({"_id": ObjectId(organization_id)})

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Delete the organization from the database
    result = await organizations_collection.delete_one({"_id": ObjectId(organization_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Delete failed, organization might not exist")

    # Return a success message
    return DeleteOrganizationResponse(message="Organization deleted successfully")

@router.post("/organization/{organization_id}/invite", response_model=InviteUserResponse)
async def invite_user_to_organization(organization_id: str, invite_request: InviteUserRequest, token: str = Depends(oauth2_scheme)):
    # Check if the organization exists
    organization = await organizations_collection.find_one({"_id": ObjectId(organization_id)})

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Send the invitation email
    user_email = invite_request.user_email
    await send_invitation_email(user_email, organization["name"])

    # Return a success message
    return InviteUserResponse(message=f"Invitation sent to {user_email} for organization '{organization['name']}'")

async def send_invitation_email(to_email: str, organization_name: str):
    # Email configuration
    smtp_server = "smtp.example.com"  # Replace with your SMTP server
    smtp_port = 587  # Port for TLS
    smtp_user = "your_email@example.com"  # Your email
    smtp_password = "your_password"  # Your email password

    # Create the email content
    subject = f"Invitation to join {organization_name}"
    body = f"You have been invited to join {organization_name}. Please click the link to accept the invitation."

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error sending email: " + str(e))