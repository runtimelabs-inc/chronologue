import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def load_grocery_scheduling(file_path: str):
    with open(file_path, 'r') as f:
        memory = json.load(f)
    r = requests.post(f"{BASE_URL}/orders", json=memory)
    r.raise_for_status()
    print("✅ Grocery scheduling memory created:", r.json())

def load_sports_schedule(file_path: str):
    with open(file_path, 'r') as f:
        memory = json.load(f)
    r = requests.post(f"{BASE_URL}/events", json=memory)
    r.raise_for_status()
    print("✅ Sports schedule memory created:", r.json())

def load_chat_history(file_path: str):
    with open(file_path, 'r') as f:
        memory = json.load(f)
    r = requests.post(f"{BASE_URL}/chats", json=memory)
    r.raise_for_status()
    print("✅ Chat history memory created:", r.json())

if __name__ == "__main__":
    # Uncomment and set correct paths
    load_grocery_scheduling('datasets/grocery_scheduling.json')
    load_sports_schedule('datasets/sports_schedule.json')
    load_chat_history('datasets/chat_history.json')
