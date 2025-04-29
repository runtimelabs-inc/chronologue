from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Literal

# Import the order memory db from orders.py for now
from api.orders import order_memory_db

router = APIRouter()

# ------------------------------
# Models
# ------------------------------

class ApprovalRequest(BaseModel):
    user_id: str
    approval_status: Literal["approved", "rejected"]
    timestamp: datetime

# ------------------------------
# Endpoints
# ------------------------------

@router.post("/orders/{order_id}/approval")
async def submit_approval(order_id: str, approval: ApprovalRequest):
    if order_id not in order_memory_db:
        raise HTTPException(status_code=404, detail="Order not found")

    # Store the approval status inside the order memory (simple for now)
    order_memory_db[order_id]["approval_status"] = approval.approval_status
    order_memory_db[order_id]["approval_timestamp"] = approval.timestamp.isoformat()

    return {"order_id": order_id, "status": "approval recorded", "approval": approval.approval_status}
