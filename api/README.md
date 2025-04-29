# Chronologue Memory Orchestration API

Chronologue provides a structured memory system and calendar integration layer for managing recurring grocery orders through conversational agents.

## Design Philosophy

Designed for agent-native architectures, Chronologue focuses on:

- Persistent memory grounding for recurring events
- Explicit user approvals before autonomous actions
- Delivery tracking and feedback collection
- Seamless calendar synchronization via dynamic .ics files

Chronologue is API-first and built for clean agent integration.

## Features

- **Grocery Memory Management**: Upload, edit, and track structured grocery lists
- **Approval Workflows**: Weekly order confirmations before purchase
- **Delivery Tracking**: Scheduled delivery windows and feedback loops
- **Calendar Synchronization**: Weekly .ics event generation
- **Developer Friendly**: Clean FastAPI endpoints, Postman Collection, OpenAPI Spec

## Running Chronologue Locally

### Installation

Install Python dependencies:


--- 



# Chronologue Memory Orchestration API

This is the API backend for managing Chronologue memory operations, including:
- Grocery memory management (orders)
- Weekly approval flows
- Delivery tracking and feedback collection
- Calendar event generation

---

## Running the API Locally

1. Install dependencies (added to requirements.txt)
   ```bash
   uv pip install fastapi uvicorn pydantic
    ```

2. Launch the API Server


```bash 
uvicorn api.main:app --reload
```

The server will run at http://127.0.0.1:8000

Swagger UI available at http://127.0.0.1:8000/docs


#### API Endpoints 

Endpoint | Method | Purpose
/api/orders | POST | Create a new grocery memory
/api/orders/{order_id} | GET | Retrieve an existing memory
/api/orders/{order_id} | PATCH | Edit memory items
/api/orders/{order_id}/approval | POST | Submit order approval
/api/feedback | POST | Submit delivery feedback


Testing the API 

You can use:

- Postman: Create requests manually

- Swagger UI: Interact directly from http://127.0.0.1:8000/docs

- Python test scripts: See test_chronologue_api.py

Example:

Create an order → Fetch it → Approve it → Submit feedback

### Developer Notes 

- Current memory store is in-memory only (order_memory_db)

- For production, swap to database or persistent key-value store

- .ics generation (calendar event sync) coming next

Full Chronologue backend working locally:
- Memory creation
- Approval confirmation
- Delivery feedback collection
