from pydantic import BaseModel
from typing import List, Optional

class GroceryItem(BaseModel):
    quantity: int
    item: str
    link: Optional[str] = None

class ApprovalSchedule(BaseModel):
    day: str
    time: str  # Format: HH:MM

class DeliverySchedule(BaseModel):
    day: str
    window_start: str  # Format: HH:MM
    window_end: str    # Format: HH:MM

class OrderMemory(BaseModel):
    user_id: str
    items: List[GroceryItem]
    approval_schedule: ApprovalSchedule
    delivery_schedule: DeliverySchedule
