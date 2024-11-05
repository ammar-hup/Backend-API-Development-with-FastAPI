# app/schemas.py
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

class ItemResponse(ItemCreate):
    id: int

    class Config:
        orm_mode = True