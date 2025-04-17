# tests/test_scheduler.py
import pytest
from calendar import scheduler

# Sample valid GPT output
VALID_GPT_OUTPUT = '''
[
    {
        "title": "Test Meeting",
        "description": "Discuss project status",
        "start": "2025-05-01T10:00:00",
        "end": "2025-05-01T10:30:00",
        "timezone": "UTC"
    }
]'''

# Sample invalid JSON
INVALID_GPT_OUTPUT = "not valid JSON"

# Missing required fields
MISSING_FIELDS_OUTPUT = '''
[
    {
        "title": "No start/end"
    }
]'''

def test_parse_valid_gpt_output():
    events = scheduler.parse_gpt_calendar_output(VALID_GPT_OUTPUT)
    assert isinstance(events, list)
    assert len(events) == 1
    assert events[0]['title'] == "Test Meeting"
    assert events[0]['start'] == "2025-05-01T10:00:00"
    assert events[0]['end'] == "2025-05-01T10:30:00"

def test_parse_invalid_gpt_output():
    events = scheduler.parse_gpt_calendar_output(INVALID_GPT_OUTPUT)
    assert events == []

def test_parse_output_missing_fields():
    events = scheduler.parse_gpt_calendar_output(MISSING_FIELDS_OUTPUT)
    assert events == []
