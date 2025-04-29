import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api"

# Step 1: Create a grocery order
order = {
    "user_id": "user_123",
    "items": [
        {"quantity": 2, "item": "Organic Blueberries"},
        {"quantity": 1, "item": "Dino Kale"}
    ],
    "approval_schedule": {
        "day": "Friday",
        "time": "09:00"
    },
    "delivery_schedule": {
        "day": "Sunday",
        "window_start": "08:00",
        "window_end": "10:00"
    }
}

r = requests.post(f"{BASE_URL}/orders", json=order)
order_id = r.json()["order_id"]
print("[Agent] Created Order ID:", order_id)

# Step 2: Fetch current order memory
r = requests.get(f"{BASE_URL}/orders/{order_id}")
order_memory = r.json()
print("[Agent] Retrieved Memory:", order_memory)

# Step 3: Simulate user approval
approval = {
    "user_id": "user_123",
    "approval_status": "approved",
    "timestamp": datetime.utcnow().isoformat()
}

r = requests.post(f"{BASE_URL}/orders/{order_id}/approval", json=approval)
print("[Agent] Approval Submitted:", r.json())

# Step 4: Simulate delivery feedback after completion
feedback = {
    "user_id": "user_123",
    "order_id": order_id,
    "feedback_text": "All groceries delivered perfectly!",
    "timestamp": datetime.utcnow().isoformat()
}

r = requests.post(f"{BASE_URL}/feedback", json=feedback)
print("[Agent] Feedback Submitted:", r.json())
