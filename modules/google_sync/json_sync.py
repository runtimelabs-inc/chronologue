import json
from schema import validate_memory_trace
from google_sync.event_utils import memory_trace_to_event

def sync_json_file(service, memory_json_path):
    with open(memory_json_path) as f:
        session = json.load(f)

    traces = session.get("memory", [])
    synced = 0

    for trace in traces:
        if validate_memory_trace(trace):
            try:
                event = memory_trace_to_event(trace)
                service.events().insert(calendarId='primary', body=event).execute()
                print(f"[✓] Synced: {event['summary']}")
                synced += 1
            except Exception as e:
                print(f"[!] Failed to sync {trace.get('id')}: {e}")

    print(f"\n[✓] {synced} events synced from {memory_json_path.name}")
