# schema.py
from typing import Dict, List
from datetime import datetime
import json
import os

# Required and allowed fields
REQUIRED_FIELDS = [
    "id",
    "type",
    "timestamp",
    "content",
    "task_id"
]


## Review allowed types (ie. priors)
ALLOWED_TYPES = {"goal", "observation", "reflection", "calendar_event"}
ALLOWED_COMPLETION_STATUSES = {"pending", "done", "scheduled", "canceled"}
ALLOWED_VISIBILITY = {"private", "shared", "public"}


def validate_memory_trace(trace: Dict) -> bool:
    """
    Validate a memory trace based on required fields, types, and optional metadata.
    Returns True if valid, False otherwise.
    """
    try:
        # Check required fields
        for field ian REQUIRED_FIELDS:
            if field not in trace:
                print(f"Missing required field: {field}")
                return False

        # Validate trace type
        if trace["type"] not in ALLOWED_TYPES:
            print(f"Invalid type: {trace['type']}")
            return False

        # Validate timestamp format
        datetime.fromisoformat(trace["timestamp"].replace("Z", "+00:00"))

        # Optional field validations
        if "importance" in trace:
            val = float(trace["importance"])
            if not (0.0 <= val <= 1.0):
                print("Importance must be between 0.0 and 1.0")
                return False

        if "collaborators" in trace and not isinstance(trace["collaborators"], list):
            print("Collaborators must be a list")
            return False

        if "embedding" in trace and not isinstance(trace["embedding"], list):
            print("Embedding must be a list of floats")
            return False

        if "completion_status" in trace and trace["completion_status"] not in ALLOWED_COMPLETION_STATUSES:
            print(f"Invalid completion_status: {trace['completion_status']}")
            return False

        if "linked_event_uid" in trace and not isinstance(trace["linked_event_uid"], str):
            print("linked_event_uid must be a string")
            return False

        if "visibility" in trace and trace["visibility"] not in ALLOWED_VISIBILITY:
            print(f"Invalid visibility: {trace['visibility']}")
            return False

    except Exception as e:
        print(f"Validation error: {e}")
        return False

    return True


def load_traces_from_json(path: str) -> List[Dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r") as f:
        return json.load(f).get("memory", [])


def validate_trace_file(path: str) -> bool:
    traces = load_traces_from_json(path)
    all_valid = True
    for trace in traces:
        is_valid = validate_memory_trace(trace)
        print(f"Trace {trace['id']}: {'✅ Valid' if is_valid else '❌ Invalid'}")
        if not is_valid:
            all_valid = False
    return all_valid


from ics import Calendar, Event
from datetime import datetime
from pathlib import Path
import pytz

def export_to_ics(trace: dict, output_path: str) -> None:
    """
    Converts a single memory trace into a .ics calendar file and saves it.

    Args:
        trace (dict): A memory trace with type 'calendar_event' and required fields.
        output_path (str): File path to save the .ics file.
    """
    cal = Calendar()
    event = Event()

    event.name = trace.get("title", "Untitled Event")
    event.description = trace.get("description", "")
    event.begin = trace["start"]
    event.end = trace["end"]

if __name__ == "__main__":
    test_path = os.path.join("..", "data", "conversation", "raw", "lab_manager_4-12.json")
    try:
        valid = validate_trace_file(test_path)
        print("\nAll traces valid " if valid else "\nSome traces are invalid ")
    except Exception as e:
        print(f"Error: {e}")


