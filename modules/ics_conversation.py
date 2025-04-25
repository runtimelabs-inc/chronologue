import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

# Function definition
function_definitions = [
    {
        "name": "filter_by_date",
        "description": "Extracts start_date and end_date to filter memory traces from a user request.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"}
            },
            "required": ["start_date", "end_date"]
        }
    }
]

# Helper: Import ICS
def parse_ics_datetime(dt_str: str) -> str:
    return datetime.strptime(dt_str.strip(), "%Y%m%dT%H%M%SZ").isoformat() + "Z"

def import_ics(filepath: str) -> List[Dict]:
    with open(filepath, "r") as f:
        content = f.read()
    events = []
    for block in content.split("BEGIN:VEVENT")[1:]:
        lines = block.strip().splitlines()
        trace = {"type": "calendar_event"}
        for line in lines:
            if line.startswith("SUMMARY:"):
                trace["title"] = line[8:].strip()
            elif line.startswith("DESCRIPTION:"):
                trace["content"] = line[12:].strip()
            elif line.startswith("DTSTART:"):
                trace["timestamp"] = parse_ics_datetime(line[8:].strip())
            elif line.startswith("DTEND:"):
                trace["end"] = parse_ics_datetime(line[6:].strip())
            elif line.startswith("UID:"):
                trace["id"] = line[4:].strip()
        if "timestamp" in trace and "end" in trace:
            start = datetime.fromisoformat(trace["timestamp"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(trace["end"].replace("Z", "+00:00"))
            trace["duration_minutes"] = int((end - start).total_seconds() / 60)
        events.append(trace)
    return events

# Helper: Filter by timestamps
def filter_by_timestamp(traces: List[Dict], start_date: str, end_date: str) -> List[Dict]:
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    return [
        trace for trace in traces
        if start <= datetime.fromisoformat(trace["timestamp"].replace("Z", "+00:00")) <= end
    ]

# Helper: Format traces for model
def format_traces_for_summary(traces: List[Dict]) -> str:
    return "\n".join(
        f"- {trace.get('title', 'Untitled')} ({trace['timestamp']}): {trace.get('content', '')}"
        for trace in traces
    )

# Summarize selected traces
def summarize_traces(traces: List[Dict]) -> str:
    context = format_traces_for_summary(traces)
    messages = [
        {
            "role": "developer",
            "content": "You are a memory summarizer. Given a list of calendar memory traces, summarize chronologically."
        },
        {
            "role": "user",
            "content": f"Here are the memory traces:\n\n{context}"
        }
    ]
    response = client.responses.create(model="gpt-4.1", input=messages)
    return response.output_text.strip()

# Parse function call
def parse_date_call(tool_calls) -> (str, str):
    if tool_calls and tool_calls[0].function.name == "filter_by_date":
        args = json.loads(tool_calls[0].function.arguments)
        return args["start_date"], args["end_date"]
    return None, None

# Main function per prompt
def summarize_events_from_prompt(user_prompt: str, traces: List[Dict]) -> Dict:
    system_message = {
        "role": "developer",
        "content": (
            "You are an assistant that extracts start_date and end_date for summarizing calendar memory traces. "
            "Output must call the function filter_by_date."
        )
    }

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[system_message, {"role": "user", "content": user_prompt}],
        tools=[{"type": "function", "function": function_definitions[0]}],
        tool_choice="auto"
    )

    start_date, end_date = parse_date_call(response.tool_calls)
    if not start_date or not end_date:
        return {
            "prompt": user_prompt,
            "summary": "Unable to determine timeframe.",
            "start_date": None,
            "end_date": None,
            "trace_ids": [],
            "error": "Missing date extraction."
        }

    filtered = filter_by_timestamp(traces, start_date, end_date)
    summary = summarize_traces(filtered) if filtered else f"No events found between {start_date} and {end_date}."

    return {
        "prompt": user_prompt,
        "start_date": start_date,
        "end_date": end_date,
        "summary": summary,
        "trace_ids": [trace["id"] for trace in filtered]
    }

# Master runner
def run_prompt_suite(data_path: str, prompt_path: str, base_output_dir: str):
    traces = import_ics(data_path)
    with open(prompt_path, "r") as f:
        prompts = json.load(f)

    results = []
    for entry in prompts:
        prompt = entry["prompt"]
        print(f"→ Running prompt: {prompt}")
        result = summarize_events_from_prompt(prompt, traces)
        result["id"] = entry.get("id")
        result["expected"] = entry.get("expected")
        results.append(result)

    # Dynamically create output filename
    base_name = Path(data_path).stem
    output_path = Path(base_output_dir) / f"{base_name}_prompt_summary_log.json"

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nPrompt log saved to {output_path}")

# --- Example usage ---

data_path = "/Users/derekrosenzweig/Documents/GitHub/chronologue/data/summary/raw_ics/wetlab_sample.ics"
prompt_path = "/Users/derekrosenzweig/Documents/GitHub/chronologue/data/summary/prompts/prompt_suite.json"
base_output_dir = "/Users/derekrosenzweig/Documents/GitHub/chronologue/data/summary/responses/"

run_prompt_suite(data_path, prompt_path, base_output_dir)
