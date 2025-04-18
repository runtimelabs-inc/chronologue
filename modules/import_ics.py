# import_ics.py

from datetime import datetime
from typing import List, Dict
import re
import json
from pathlib import Path

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

def save_events_to_json(events: List[Dict], output_path: str) -> None:
    """Save the list of events to a JSON file."""
    with open(output_path, 'w') as json_file:
        json.dump(events, json_file, indent=4)
    print(f"→ Events saved to {output_path}")

def import_ics_from_directory(input_dir: Path, output_dir: Path) -> None:
    """Import events from all iCalendar (.ics) files in a directory and save each to a JSON file."""
    for ics_file in input_dir.glob("*.ics"):
        print(f"→ Reading iCalendar file: {ics_file}")
        events = import_ics(str(ics_file))
        # Generate output filename based on input filename
        output_file = output_dir / (ics_file.stem + ".json")
        save_events_to_json(events, str(output_file))

if __name__ == "__main__":
    
    input_dir = Path("/Users/derekrosenzweig/Documents/GitHub/chronologue/data/calendar/raw")
    output_dir = Path("/Users/derekrosenzweig/Documents/GitHub/chronologue/data/calendar/processed")
    import_ics_from_directory(input_dir, output_dir)

    