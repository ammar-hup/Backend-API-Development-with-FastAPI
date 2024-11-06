from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: int
    name: str
    email: str
    password: str  # Store hashed passwords, not plain text

class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float