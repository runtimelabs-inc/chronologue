from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from export_ics import generate_ics_string, write_consolidated_ics

from schema import validate_memory_trace
from pathlib import Path


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


INPUT_DIR = Path("/Users/derekrosenzweig/Documents/GitHub/chronologue/data/conversation/raw")
OUTPUT_DIR = Path("/Users/derekrosenzweig/Documents/GitHub/chronologue/data/conversation/api-processed")

def call_openai_tool(trace: dict) -> dict:
    """Send the trace to OpenAI tool calling and get processed arguments back."""
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": "Generate a calendar event for this lab memory."}],
        tools=[{
            "type": "function",
            "function": {
                "name": "generate_event_ics",
                "description": "Generate an ICS VEVENT string from a structured memory trace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "trace": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "timestamp": {"type": "string", "format": "date-time"},
                                "content": {"type": "string"},
                                "task_id": {"type": "string"},
                                "location": {"type": "string"},
                                "chat_url": {"type": "string"},
                                "linked_event_uid": {"type": "string"},
                            },
                            "required": ["timestamp", "content", "task_id"]
                        }
                    },
                    "required": ["trace"]
                }
            }
        }],
        tool_choice={
            "type": "function",
            "function": {
                "name": "generate_event_ics",
                "arguments": json.dumps({"trace": trace})
            }
        }
    )
    tool_args = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
    return tool_args.get("trace", {})

def convert_json_folder_to_ics_with_tool_call(input_dir: Path, output_dir: Path):
    json_files = sorted(input_dir.glob("*.json"))
    if not json_files:
        print(f"[!] No JSON files found in {input_dir}")
        return

    for json_file in json_files:
        with open(json_file) as f:
            data = json.load(f)

        traces = data.get("memory", [])
        vevents = []

        for trace in traces:
            if not all(k in trace for k in ("timestamp", "content", "task_id")):
                print(f"[!] Skipping incomplete trace in {json_file.name}")
                continue

            
            if "id" not in trace:
                trace["id"] = f"{trace['task_id']}_{trace['timestamp'].replace(':', '').replace('-', '')}"

            try:
                processed_trace = call_openai_tool(trace)
                if validate_memory_trace(processed_trace):
                    vevent = generate_ics_string(processed_trace)
                    vevents.append(vevent)

                    
                else:
                    print(f"[!] Trace failed validation after tool call: {trace.get('id', 'UNKNOWN')}")
            except Exception as e:
                print(f"[!] Error processing trace {trace.get('id', 'UNKNOWN')}: {e}")

        if vevents:
            output_filename = json_file.stem + ".ics"
            output_path = output_dir / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_consolidated_ics(vevents, output_path)
        else:
            print(f"[!] No valid ICS events for {json_file.name}")

if __name__ == "__main__":
    convert_json_folder_to_ics_with_tool_call(INPUT_DIR, OUTPUT_DIR)