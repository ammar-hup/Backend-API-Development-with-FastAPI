# app/routes.py
from fastapi import APIRouter
from .models import Item
from typing import List

router = APIRouter()

items = []

@router.post("/items/", response_model=Item)
def create_item(item: Item):
    items.append(item)
    return item

@router.get("/items/", response_model=List[Item])
def read_items():
    return items