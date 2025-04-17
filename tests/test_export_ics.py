# tests/test_export_ics.py
import os
import sys

# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.schema import validate_memory_trace

def test_generate_ics_string():
    event = {
        "title": "Test ICS Export",
        "description": "Test exporting an event to .ics format.",
        "start": "2025-05-01T10:00:00",
        "end": "2025-05-01T10:30:00",
        "location": "Zoom",
        "organizer_email": "agent@memorysystem.ai"
    }
    ics_string = export_ics.generate_ics_string(event)
    assert "BEGIN:VEVENT" in ics_string
    assert "SUMMARY:Test ICS Export" in ics_string
    assert "DESCRIPTION:Test exporting an event to .ics format." in ics_string
    assert "LOCATION:Zoom" in ics_string


def test_export_to_ics(tmp_path):
    event = {
        "title": "Test Write ICS",
        "description": "Check that file is written correctly.",
        "start": "2025-05-01T14:00:00",
        "end": "2025-05-01T14:30:00",
        "location": "Online"
    }
    file_path = tmp_path / "test_event.ics"
    export_ics.export_to_ics(event, str(file_path))

    assert file_path.exists()
    content = file_path.read_text()
    assert "BEGIN:VCALENDAR" in content
    assert "SUMMARY:Test Write ICS" in content
    assert "LOCATION:Online" in content