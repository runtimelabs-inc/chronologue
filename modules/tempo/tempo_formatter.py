
from datetime import datetime, timezone
import re

def generate_tempo_token(dt: datetime, now: datetime) -> str:
    delta = dt - now
    time_str = dt.strftime('%-I:%M%p').lower()

    if abs(delta.days) < 1:
        return f"<today@{time_str}>"
    elif delta.days == -1:
        return f"<yesterday@{time_str}>"
    elif delta.days == 1:
        return f"<tomorrow@{time_str}>"
    else:
        day = dt.strftime('%A').lower()
        return f"<{day}@{time_str}>"

def format_memory_trace(trace: dict, now: datetime = None) -> str:
    if now is None:
        now = datetime.now(timezone.utc)

    timestamp = trace.get("timestamp")
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    tempo = generate_tempo_token(dt, now)
    mtype = trace.get("type", "note")
    content = trace.get("title", "")
    uid = trace.get("uid", "")
    duration = trace.get("duration", "")
    links = trace.get("linked_memory", [])

    extras = []
    if uid:
        extras.append(f"UID: {uid}")
    if duration:
        extras.append(f"duration={duration}m")
    if links:
        extras.append(f"links={','.join(links)}")

    extra_str = f"[{', '.join(extras)}] " if extras else ""
    return f"{extra_str}{dt.isoformat()}Z {tempo} [{mtype}]: {content}"


# -------------------------------
# Example + Test
# -------------------------------
def test_format_memory_trace():
    now = datetime(2025, 5, 2, 9, 0, tzinfo=timezone.utc)  # fixed reference point

    trace = {
        "type": "goal",
        "title": "Submit IRB application",
        "timestamp": "2025-05-02T09:00:00Z",
        "duration": 60,
        "uid": "goal_043",
        "linked_memory": ["trace_038", "trace_039"]
    }

    output = format_memory_trace(trace, now=now)
    expected = (
        "[UID: goal_043, duration=60m, links=trace_038,trace_039] "
        "2025-05-02T09:00:00+00:00Z <today@9:00am> [goal]: Submit IRB application"
    )

    assert output == expected, f"Test failed:\nExpected:\n{expected}\nGot:\n{output}"
    print("Test passed. Output:")
    print(output)

if __name__ == "__main__":
    test_format_memory_trace()
