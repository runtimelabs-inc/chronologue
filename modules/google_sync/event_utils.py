from datetime import datetime, timedelta

def memory_trace_to_event(trace):
    start = trace["timestamp"]
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    end_dt = start_dt + timedelta(minutes=30)

    summary = f"[{trace['type'].upper()}] {trace['content'][:40]}..."
    description = trace["content"]

    meta = []
    for field in ["task_id", "importance", "completion_status", "source"]:
        if field in trace:
            meta.append(f"{field.replace('_',' ').title()}: {trace[field]}")

    full_description = description + ("\n\n" + "\n".join(meta) if meta else "")

    return {
        "id": trace.get("linked_event_uid", f"{trace['id']}@memorysystem.ai").replace("@", "_"),
        "summary": summary,
        "description": full_description,
        "start": {"dateTime": start, "timeZone": "UTC"},
        "end": {"dateTime": end_dt.isoformat() + "Z", "timeZone": "UTC"},
    }
