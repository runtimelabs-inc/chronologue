import requests

BASE_URL = "http://127.0.0.1:8000/api"

# 1. Create a grocery memory
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

# Create order
r = requests.post(f"{BASE_URL}/orders", json=order)
print("Create Order Response:", r.json())

# Extract order_id
order_id = r.json()["order_id"]

# Fetch created order
r = requests.get(f"{BASE_URL}/orders/{order_id}")
print("Fetched Order Memory:", r.json())

# Approve order (this will fail if /approval endpoint not yet built!)
approval = {
    "user_id": "user_123",
    "approval_status": "approved",
    "timestamp": "2025-05-01T09:05:00Z"
}

try:
    r = requests.post(f"{BASE_URL}/orders/{order_id}/approval", json=approval)
    print("Approval Response:", r.json())
except Exception as e:
    print("Approval failed (likely because /approval not built yet):", e)
