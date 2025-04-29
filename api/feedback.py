from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

# Import the order memory db from orders.py for now
from api.orders import order_memory_db

router = APIRouter()

# ------------------------------
# Models
# ------------------------------

class FeedbackSubmission(BaseModel):
    user_id: str
    order_id: str
    feedback_text: str
    timestamp: datetime

# ------------------------------
# Endpoints
# ------------------------------

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackSubmission):
    if feedback.order_id not in order_memory_db:
        raise HTTPException(status_code=404, detail="Order not found")

    # Append feedback inside the order memory (for simplicity)
    if "feedback" not in order_memory_db[feedback.order_id]:
        order_memory_db[feedback.order_id]["feedback"] = []

    order_memory_db[feedback.order_id]["feedback"].append({
        "user_id": feedback.user_id,
        "feedback_text": feedback.feedback_text,
        "timestamp": feedback.timestamp.isoformat()
    })

    return {"order_id": feedback.order_id, "status": "feedback recorded"}
