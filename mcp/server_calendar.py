from mcp.server.fastmcp import FastMCP
from pathlib import Path
from datetime import datetime, timedelta
import json
import os

# Initialize the MCP server
mcp = FastMCP("CalendarMemoryTools")

# --- Inlined ICS generation logic ---

def generate_uid(title: str, date_str: str) -> str:
    base = title.lower().replace(" ", "_").replace("/", "_").replace("°", "").replace("#", "")
    return f"{base}-{date_str}@memorysystem.ai"

def datetime_to_ics(dt: str) -> str:
    return datetime.fromisoformat(dt.replace("Z", "+00:00")).strftime("%Y%m%dT%H%M%SZ")

def generate_ics_string(trace: dict) -> str:
    start_iso = trace["timestamp"]
    start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    end_dt = start_dt + timedelta(minutes=15)

    start = start_dt.strftime("%Y%m%dT%H%M%SZ")
    end = end_dt.strftime("%Y%m%dT%H%M%SZ")
    summary = trace["content"][:40] + ("..." if len(trace["content"]) > 40 else "")
    chat_url = trace.get("chat_url", "https://chat.openai.com/share/example-link")
    full_description = f"{trace['content']}\\nChat log: {chat_url}"

    summary = summary.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
    full_description = full_description.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")

    dtstamp = "20250401T080000Z"
    uid = trace.get("linked_event_uid") or generate_uid(trace["task_id"], start[:8])
    location = trace.get("location", "")

    return f"""BEGIN:VEVENT
                UID:{uid}
                DTSTAMP:{dtstamp}
                DTSTART:{start}
                DTEND:{end}
                SUMMARY:{summary}
                DESCRIPTION:{full_description}
                LOCATION:{location}
                STATUS:CONFIRMED
                END:VEVENT"""

def write_consolidated_ics(events: list[str], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    calendar_header = "BEGIN:VCALENDAR\rVERSION:2.0\rPRODID:-//CalendarMemorySystem//EN\r"
    calendar_footer = "\rEND:VCALENDAR"
    events_block = "".join(events)
    calendar_block = calendar_header + events_block + calendar_footer

    with open(output_path, "w", newline='\r\n') as f:
        f.write(calendar_block)

# --- MCP Tools and Resources ---

# @mcp.tool()
# def convert_trace_to_ics(trace_json: str) -> str:
#     """Convert a single memory trace JSON string to an ICS VEVENT string"""
#     trace = json.loads(trace_json)
#     return generate_ics_string(trace)


@mcp.tool()
def convert_trace_to_ics(trace: dict) -> str:
    """Convert a memory trace dictionary to an ICS VEVENT string"""
    return generate_ics_string(trace)

@mcp.tool()
def batch_convert_json_to_ics(input_dir: str, output_dir: str) -> str:
    """Convert a folder of JSON memory files into .ics files"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    if not input_path.exists():
        return f"Input directory not found: {input_dir}"

    json_files = sorted(input_path.glob("*.json"))
    if not json_files:
        return f"No JSON files found in {input_dir}"

    for json_file in json_files:
        with open(json_file) as f:
            data = json.load(f)

        traces = data.get("memory", [])
        vevents = []
        for trace in traces:
            try:
                vevents.append(generate_ics_string(trace))
            except KeyError as e:
                continue

        if vevents:
            output_filename = json_file.stem + ".ics"
            write_consolidated_ics(vevents, output_path / output_filename)

    return f"ICS files written to {output_dir}"

@mcp.resource("calendar://test_ics_generation")
def test_ics_generation() -> str:
    """Return a sample VEVENT string to verify ICS conversion works"""
    sample_trace = {
        "id": "sample-001",
        "type": "observation",
        "timestamp": "2024-04-07T09:00:00Z",
        "content": "Incubator #3 temperature rose unexpectedly.",
        "task_id": "lab_ops",
        "location": "wetlab_sync"
    }
    return generate_ics_string(sample_trace)

@mcp.resource("calendar://tool_summary")
def tool_summary() -> str:
    """List available tools and resources"""
    tool_names = [tool.name for tool in mcp.tool]
    resource_names = list(mcp.resources.keys())
    return json.dumps({
        "tools": tool_names,
        "resources": resource_names
    }, indent=2)
