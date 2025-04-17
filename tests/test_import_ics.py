# tests/test_import_ics.py
from calendar import import_ics

def test_parse_ics_event():
    ics_event = """
SUMMARY:Review Planning
DESCRIPTION:Weekly review of upcoming tasks
DTSTART:20250501T100000Z
DTEND:20250501T103000Z
UID:review-20250501@memory.ai
LOCATION:https://zoom.us/j/12345
ORGANIZER;CN=Memory Agent:mailto:agent@memorysystem.ai
"""
    event = import_ics.parse_ics_event(ics_event)
    assert event['title'] == "Review Planning"
    assert event['description'] == "Weekly review of upcoming tasks"
    assert event['start'] == "2025-05-01T10:00:00Z"
    assert event['end'] == "2025-05-01T10:30:00Z"
    assert event['location'] == "https://zoom.us/j/12345"
    assert event['uid'] == "review-20250501@memory.ai"
    assert event['organizer_email'] == "agent@memorysystem.ai"


def test_import_ics(tmp_path):
    ics_content = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MemorySystem//EN
BEGIN:VEVENT
SUMMARY:Test Import
DESCRIPTION:Test importing an event from .ics
DTSTART:20250502T120000Z
DTEND:20250502T123000Z
UID:test-import-20250502@memory.ai
LOCATION:Zoom
ORGANIZER;CN=Memory Agent:mailto:agent@memorysystem.ai
END:VEVENT
END:VCALENDAR
"""
    file_path = tmp_path / "test_import.ics"
    file_path.write_text(ics_content)

    events = import_ics.import_ics(str(file_path))
    assert len(events) == 1
    assert events[0]['title'] == "Test Import"
    assert events[0]['start'] == "2025-05-02T12:00:00Z"