# tests/test_export_ics.py

# PYTHONPATH=. pytest tests/test_export_ics.py

import pytest
from pathlib import Path
from chronologue_modules.export_ics import generate_ics_string, write_consolidated_ics

def test_generate_ics_default_duration():
    trace = {
        "id": "default-duration-test",
        "type": "calendar_event",
        "timestamp": "2025-04-25T08:00:00Z",
        "content": "Morning standup with team",
        "task_id": "team_sync",
        "location": "zoom_link_here"
    }

    ics = generate_ics_string(trace)
    assert "DTSTART:20250425T080000Z" in ics
    assert "DTEND:20250425T083000Z" in ics  # Default is 30 minutes
    assert "SUMMARY:Morning standup with team" in ics

def test_generate_ics_custom_duration_with_long_summary():
    trace = {
        "id": "custom-duration-test",
        "type": "calendar_event",
        "timestamp": "2025-04-25T10:00:00Z",
        "content": "Deep work session on CUDA optimization and benchmarking kernels",
        "task_id": "gpu_project",
        "location": "office",
        "duration_minutes": 90
    }

    ics = generate_ics_string(trace)
    assert "DTSTART:20250425T100000Z" in ics
    assert "DTEND:20250425T113000Z" in ics
    assert "SUMMARY:Deep work session on CUDA optimizati..." in ics
def test_generate_ics_custom_duration_with_long_summary():
    trace = {
        "id": "custom-duration-test",
        "type": "calendar_event",
        "timestamp": "2025-04-25T10:00:00Z",
        "content": "Deep work session on CUDA optimization and benchmarking kernels",
        "task_id": "gpu_project",
        "location": "office",
        "duration_minutes": 90
    }

    ics = generate_ics_string(trace)
    assert "DTSTART:20250425T100000Z" in ics
    assert "DTEND:20250425T113000Z" in ics
    assert "\nSUMMARY:Deep work session on CUDA optimizati..." in ics


def test_generate_ics_summary_exactly_40_chars():
    trace = {
        "id": "exact-length-test",
        "type": "calendar_event",
        "timestamp": "2025-04-25T11:00:00Z",
        "content": "This string has exactly forty characters!",
        "task_id": "length_test",
        "location": "test_lab",
        "duration_minutes": 45
    }

    ics = generate_ics_string(trace)
    assert "DTSTART:20250425T110000Z" in ics
    assert "DTEND:20250425T114500Z" in ics
    assert "\nSUMMARY:This string has exactly forty characters!" in ics
