from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4

router = APIRouter()

order_memory_db = {}

class GroceryItem(BaseModel):
    quantity: int
    item: str
    link: Optional[str] = None

class ApprovalSchedule(BaseModel):
    day: str
    time: str

class DeliverySchedule(BaseModel):
    day: str
    window_start: str
    window_end: str

class OrderMemory(BaseModel):
    user_id: str
    items: List[GroceryItem]
    approval_schedule: ApprovalSchedule
    delivery_schedule: DeliverySchedule

@router.post("/orders")
async def create_order(order: OrderMemory):
    order_id = str(uuid4())
    order_memory_db[order_id] = order.dict()
    return {"order_id": order_id, "status": "created"}

@router.get("/orders/{order_id}")
async def get_order(order_id: str):
    order = order_memory_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.patch("/orders/{order_id}")
async def edit_order(order_id: str, updated_items: List[GroceryItem]):
    if order_id not in order_memory_db:
        raise HTTPException(status_code=404, detail="Order not found")
    order_memory_db[order_id]["items"] = [item.dict() for item in updated_items]
    return {"order_id": order_id, "status": "updated"}
