from datetime import datetime
from typing import List, Dict
import re


def parse_ics_datetime(dt_str: str) -> str:
    return datetime.strptime(dt_str.strip(), "%Y%m%dT%H%M%SZ").isoformat() + "Z"

def parse_ics_event(ics_text: str) -> Dict:
    fields = {
        "title": None,
        "description": None,
        "start": None,
        "end": None,
        "location": None,
        "uid": None,
        "organizer_email": None
    }

    for line in ics_text.splitlines():
        if line.startswith("SUMMARY:"):
            fields["title"] = line[len("SUMMARY:"):].strip()
        elif line.startswith("DESCRIPTION:"):
            fields["description"] = line[len("DESCRIPTION:"):].strip()
        elif line.startswith("DTSTART:"):
            fields["start"] = parse_ics_datetime(line[len("DTSTART:"):])
        elif line.startswith("DTEND:"):
            fields["end"] = parse_ics_datetime(line[len("DTEND:"):])
        elif line.startswith("UID:"):
            fields["uid"] = line[len("UID:"):].strip()
        elif line.startswith("LOCATION:"):
            fields["location"] = line[len("LOCATION:"):].strip()
        elif line.startswith("ORGANIZER;CN="):
            match = re.search(r"mailto:(.*)", line)
            if match:
                fields["organizer_email"] = match.group(1)

    return {k: v for k, v in fields.items() if v is not None}


def import_ics(filepath: str) -> List[Dict]:
    with open(filepath, "r") as f:
        content = f.read()

    events = []
    for match in re.finditer(r"BEGIN:VEVENT(.*?)END:VEVENT", content, re.DOTALL):
        event_block = match.group(1)
        event_data = parse_ics_event(event_block)
        events.append(event_data)

    print(f"Imported {len(events)} event(s) from {filepath}")
    return events
