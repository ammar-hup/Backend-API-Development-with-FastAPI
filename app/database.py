from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Connect to MongoDB running in a Docker container
client = AsyncIOMotorClient("mongodb://mongo:27017")  
database = client.users_db  # Create or get the database
users_collection = database.users  # Create or get the users collection

# Helper function to convert MongoDB documents to Pydantic models
def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),  # Convert ObjectId to string
        "name": user["name"],
        "email": user["email"],
        "refresh_token": user.get("refresh_token", None)  # Handle missing refresh_token
    }