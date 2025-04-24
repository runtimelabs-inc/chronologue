"""
generalize_trace.py

- Loads a structured memory trace (from planner or raw user input).
- Generates:
  1. A personalized agent-facing response.
  2. An anonymized, generalized trace.
- Supports federated sharing, reusable workflows, or trace replay.
"""

import openai
from modules.schema import validate_memory_trace
from datetime import datetime
import json

openai.api_key = "your-api-key"

def generate_personal_response(content: str) -> str:
    prompt = f"Here’s a user memory: \"{content}\".\nGive a brief, helpful response suggesting a next step."
    res = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return res["choices"][0]["message"]["content"].strip()

def generate_generalized_trace(content: str) -> dict:
    prompt = (
        f"Generalize the following memory. Remove all names, locations, or identifiers. "
        f"Summarize it and include 3-5 tags in brackets.\n\n\"{content}\""
    )
    res = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    raw = res["choices"][0]["message"]["content"].strip()

    # Simple split for demonstration purposes (custom parser may be needed)
    parts = raw.split("\n")
    summary = parts[0].strip()
    tags = []
    for part in parts:
        if part.startswith("[") and part.endswith("]"):
            tags = [tag.strip() for tag in part.strip("[]").split(",")]

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": summary,
        "tags": tags,
        "source": "generalized"
    }

def process_trace(trace: dict) -> tuple:
    validate_memory_trace(trace)
    content = trace.get("content", "")
    personal_response = generate_personal_response(content)
    generalized = generate_generalized_trace(content)
    return personal_response, generalized

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generalize and personalize a trace.")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSON memory trace.")
    parser.add_argument("--output", type=str, required=True, help="Path to write generalized trace.")
    args = parser.parse_args()

    with open(args.input, "r") as f:
        trace = json.load(f)

    response, generalized_trace = process_trace(trace)

    with open(args.output, "w") as f:
        json.dump(generalized_trace, f, indent=2)

    print("== Personal Response ==")
    print(response)
    print("\n== Generalized Trace written to ==", args.output)
