from typing import Dict, List
from datetime import datetime
import json
import os

# Allowed values for trace fields
REQUIRED_FIELDS = ["id", "type", "timestamp", "content", "task_id"]
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
        for field in REQUIRED_FIELDS:
            if field not in trace:
                print(f"[!] Missing required field: {field}")
                return False

        # Validate trace type
        if trace["type"] not in ALLOWED_TYPES:
            print(f"[!] Invalid type: {trace['type']}")
            return False

        # Validate timestamp
        datetime.fromisoformat(trace["timestamp"].replace("Z", "+00:00"))

        # Optional field: importance
        if "importance" in trace:
            importance = float(trace["importance"])
            if not (0.0 <= importance <= 1.0):
                print("[!] Importance must be between 0.0 and 1.0")
                return False

        # Optional field: collaborators
        if "collaborators" in trace and not isinstance(trace["collaborators"], list):
            print("[!] Collaborators must be a list")
            return False

        # Optional field: embedding
        if "embedding" in trace and not isinstance(trace["embedding"], list):
            print("[!] Embedding must be a list of floats")
            return False

        # Optional field: completion_status
        if "completion_status" in trace and trace["completion_status"] not in ALLOWED_COMPLETION_STATUSES:
            print(f"[!] Invalid completion_status: {trace['completion_status']}")
            return False

        # Optional field: visibility
        if "visibility" in trace and trace["visibility"] not in ALLOWED_VISIBILITY:
            print(f"[!] Invalid visibility: {trace['visibility']}")
            return False

        # Optional field: linked_event_uid
        if "linked_event_uid" in trace and not isinstance(trace["linked_event_uid"], str):
            print("[!] linked_event_uid must be a string")
            return False

        # Optional field: duration_minutes
        if "duration_minutes" in trace:
            duration = int(trace["duration_minutes"])
            if duration <= 0 or duration > 1440:
                print("[!] duration_minutes must be a positive integer <= 1440")
                return False

    except Exception as e:
        print(f"[!] Validation error: {e}")
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
        print(f"Trace {trace['id']}: {'Valid' if is_valid else 'Invalid'}")
        if not is_valid:
            all_valid = False
    return all_valid


# Optional: ICS export example (not actively used if using custom writer)
from ics import Calendar, Event
from pathlib import Path

def export_to_ics(trace: dict, output_path: str) -> None:
    """
    Converts a single memory trace into a .ics calendar file and saves it.
    """
    cal = Calendar()
    event = Event()

    event.name = trace.get("title", "Untitled Event")
    event.description = trace.get("description", "")
    event.begin = trace["start"]
    event.end = trace["end"]

    cal.events.add(event)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.writelines(cal.serialize_iter())

if __name__ == "__main__":
    test_path = os.path.join("..", "data", "conversation", "raw", "lab_manager_4-12.json")
    try:
        valid = validate_trace_file(test_path)
        print("\nAll traces valid" if valid else "\nSome traces are invalid")
    except Exception as e:
        print(f"Error: {e}")
