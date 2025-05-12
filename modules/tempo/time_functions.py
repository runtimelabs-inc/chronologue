# uvicorn modules.tempo.time_functions:app --reload --port 8001


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid
import pytz

app = FastAPI()
timers = {}  # In-memory timer store (replace with persistent store as needed)

# ----------------------------
# Core Timekeeping Functions
# ----------------------------

def get_current_time(timezone: str = 'UTC') -> str:
    """Returns current time in ISO format."""
    now = datetime.now(pytz.timezone(timezone))
    return now.isoformat()

def generate_uuid() -> str:
    """Returns a new UUID."""
    return str(uuid.uuid4())

def start_timer(task_id: str) -> str:
    """Starts a timer for a given task."""
    timers[task_id] = datetime.utcnow()
    return f"Timer started for task {task_id}."

def stop_timer(task_id: str) -> dict:
    """Stops a timer and returns elapsed time."""
    if task_id not in timers:
        raise HTTPException(status_code=404, detail="Timer not found.")
    start_time = timers.pop(task_id)
    elapsed = datetime.utcnow() - start_time
    return {
        "task_id": task_id,
        "elapsed_seconds": round(elapsed.total_seconds(), 2),
        "start_time": start_time.isoformat(),
        "stop_time": datetime.utcnow().isoformat()
    }

def log_time(task_id: str, duration_minutes: float) -> dict:
    """Logs manual duration for a task."""
    return {
        "task_id": task_id,
        "logged_duration_minutes": duration_minutes,
        "logged_at": datetime.utcnow().isoformat()
    }

# ----------------------------
# API Schemas
# ----------------------------

class TimezoneInput(BaseModel):
    timezone: str = 'UTC'

class TaskIDInput(BaseModel):
    task_id: str

class LogTimeInput(BaseModel):
    task_id: str
    duration_minutes: float

# ----------------------------
# FastAPI Routes
# ----------------------------

@app.post("/get_current_time")
def api_get_current_time(input: TimezoneInput):
    return {"timestamp": get_current_time(input.timezone)}

@app.get("/generate_uuid")
def api_generate_uuid():
    return {"uuid": generate_uuid()}

@app.post("/start_timer")
def api_start_timer(input: TaskIDInput):
    return {"message": start_timer(input.task_id)}

@app.post("/stop_timer")
def api_stop_timer(input: TaskIDInput):
    return stop_timer(input.task_id)

@app.post("/log_time")
def api_log_time(input: LogTimeInput):
    return log_time(input.task_id, input.duration_minutes)

# ----------------------------
# OpenAI Tool Definitions
# ----------------------------

openai_tool_definitions = [
    {
        "name": "get_current_time",
        "description": "Returns the current timestamp in ISO 8601 format.",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Timezone, e.g., 'America/Los_Angeles'. Defaults to UTC.",
                    "default": "UTC"
                }
            }
        }
    },
    {
        "name": "generate_uuid",
        "description": "Generates a unique identifier for a task or event.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "start_timer",
        "description": "Starts a timer for a given task_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "stop_timer",
        "description": "Stops a running timer and returns the elapsed time.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "log_time",
        "description": "Manually logs time spent on a task.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "duration_minutes": {"type": "number"}
            },
            "required": ["task_id", "duration_minutes"]
        }
    }
]
