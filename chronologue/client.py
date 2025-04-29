import requests
from datetime import datetime
from typing import List, Optional
from chronologue.models import OrderMemory, GroceryItem

class ChronologueClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def create_order(self, order: OrderMemory) -> str:
        r = requests.post(f"{self.base_url}/api/orders", json=order.dict())
        r.raise_for_status()
        return r.json()["order_id"]

    def get_order(self, order_id: str) -> dict:
        r = requests.get(f"{self.base_url}/api/orders/{order_id}")
        r.raise_for_status()
        return r.json()

    def edit_order(self, order_id: str, updated_items: List[GroceryItem]) -> dict:
        r = requests.patch(
            f"{self.base_url}/api/orders/{order_id}",
            json=[item.dict() for item in updated_items]
        )
        r.raise_for_status()
        return r.json()

    def submit_approval(self, order_id: str, user_id: str, approval_status: str) -> dict:
        payload = {
            "user_id": user_id,
            "approval_status": approval_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        r = requests.post(f"{self.base_url}/api/orders/{order_id}/approval", json=payload)
        r.raise_for_status()
        return r.json()

    def submit_feedback(self, order_id: str, user_id: str, feedback_text: str) -> dict:
        payload = {
            "user_id": user_id,
            "order_id": order_id,
            "feedback_text": feedback_text,
            "timestamp": datetime.utcnow().isoformat()
        }
        r = requests.post(f"{self.base_url}/api/feedback", json=payload)
        r.raise_for_status()
        return r.json()
