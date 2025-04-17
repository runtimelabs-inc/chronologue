from datetime import datetime
from typing import List, Dict
import re

def parse_ics_datetime(dt_str: str) -> str:
    """Convert iCalendar datetime string to ISO 8601 format."""
    return datetime.strptime(dt_str.strip(), "%Y%m%dT%H%M%SZ").isoformat() + "Z"

def parse_ics_event(ics_text: str) -> Dict:
    """Parse a single VEVENT block from an iCalendar file into a dictionary."""
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
    """Import events from an iCalendar (.ics) file."""
    print(f"→ Reading iCalendar file: {filepath}")
    with open(filepath, "r") as f:
        content = f.read()

    events = []
    for match in re.finditer(r"BEGIN:VEVENT(.*?)END:VEVENT", content, re.DOTALL):
        event_block = match.group(1)
        event_data = parse_ics_event(event_block)
        events.append(event_data)
        print(f"→ Parsed event: {event_data.get('title', 'Untitled')}")

    print(f"→ Imported {len(events)} event(s) from {filepath}")
    return events

if __name__ == "__main__":
    
    filepath = "/Users/derekrosenzweig/Documents/GitHub/Chronologue/data/calendar/raw/lab_manager_4-12.ics"  
    events = import_ics(filepath)
    for event in events:
        print(event)