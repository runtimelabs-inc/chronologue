import re
import json
from openai import OpenAI

client = OpenAI()

# Default trace sets
TEST_TRACES = [
    {"id": "t001", "content": "Watch an NBA basketball game from start to finish"},
    {"id": "t002", "content": "Cook 1 lb of salmon in the oven at 400°F"},
    {"id": "t003", "content": "Run a standard 5K race at moderate pace"},
    {"id": "t004", "content": "Boil 3 eggs until hard boiled"},
    {"id": "t005", "content": "Write a two-page lab report summarizing recent wet lab results"},
    {"id": "t006", "content": "Set up a PCR run for 12 samples and clean up workspace"},
    {"id": "t007", "content": "Weekly sync with team to discuss project updates"},
    {"id": "t008", "content": "Organize your desk and digital workspace for better productivity"},
    {"id": "t009", "content": "Think through the research plan for a new grant proposal"},
    {"id": "t010", "content": "Reflect on last week's progress and write your thoughts"},
]

COOKING_TRACES = [
    {"id": "c001", "content": "Cook 1 lb of salmon at 400°F in the oven"},
    {"id": "c002", "content": "Bake 2 lbs of bone-in chicken thighs at 375°F"},
    {"id": "c003", "content": "Roast a 3 lb pork tenderloin at 425°F"},
    {"id": "c004", "content": "Bake chocolate chip cookies at 350°F"},
    {"id": "c005", "content": "Bake a 9-inch quiche at 375°F"},
    {"id": "c006", "content": "Broil asparagus at 500°F"},
    {"id": "c007", "content": "Bake lasagna at 375°F"},
    {"id": "c008", "content": "Roast brussels sprouts at 400°F"},
    {"id": "c009", "content": "Reheat frozen pizza at 450°F"},
    {"id": "c010", "content": "Bake sourdough bread at 475°F"}
]


def parse_duration_response(response: str) -> int | None:
    response = response.lower().strip()
    try:
        if match := re.match(r"([\d.]+)\s*(minute|minutes|min)", response):
            return int(float(match.group(1)))
        elif match := re.match(r"([\d.]+)\s*(hour|hours|hr|hrs)", response):
            return int(float(match.group(1)) * 60)
        elif match := re.match(r"([\d.]+)\s*(day|days)", response):
            return int(float(match.group(1)) * 1440)
        elif match := re.match(r"([\d.]+)\s*(second|seconds|sec)", response):
            return max(1, int(float(match.group(1)) / 60))
        elif response.isdigit():
            return int(response)
    except Exception:
        return None
    return None


def estimate_duration_with_gpt(trace: dict, model: str = "gpt-4.1") -> str:
    prompt = f"""Estimate the duration of the following task. 
Respond with a single number and time unit (e.g. "30 minutes", "1.5 hours", "2 days", or "45 seconds").
If unsure, respond with "0 minutes".

Task:
"{trace['content']}"
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a scheduling assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[!] OpenAI error on trace {trace['id']}: {e}")
        return None


def evaluate_traces(traces: list[dict], label: str):
    print(f"\n=== Evaluating: {label} ===")
    print("Trace ID | Raw Response | Parsed Minutes")
    print("-" * 60)
    for trace in traces:
        raw = estimate_duration_with_gpt(trace)
        parsed = parse_duration_response(raw) if raw else None
        print(f"{trace['id']} | {raw or 'ERROR'} | {parsed if parsed is not None else 'INVALID'}")


def load_traces_from_json(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


if __name__ == "__main__":
    # Evaluate built-in test sets first
    evaluate_traces(TEST_TRACES, label="General Tasks")
    evaluate_traces(COOKING_TRACES, label="Cooking Tasks")



    # # Optional: evaluate new uploaded file
    # try:
    #     external_traces = load_traces_from_json("cooking_traces.json")
    #     evaluate_traces(external_traces, label="Uploaded JSON File: cooking_traces.json")
    # except FileNotFoundError:
    #     print("\n[!] No external JSON file found (cooking_traces.json not loaded)")
utils/duration