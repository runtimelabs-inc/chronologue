# generate_tempo_context.py

from ics import Calendar
from datetime import datetime
from pathlib import Path
import re
import argparse

# === Tempo Token Encoder === #
def generate_tempo_tokens(event):
    tokens = []
    start = event.begin.datetime
    end = event.end.datetime

    # Absolute datetime token
    tokens.append(f"<tempo:{start.strftime('%Y-%m-%dT%H:%MZ')}>")

    # Weekday token
    tokens.append(f"<tempo:{start.strftime('%A')}>")

    # Time-of-day bucket
    hour = start.hour
    if hour < 6:
        tokens.append("<tempo:EarlyMorning>")
    elif hour < 12:
        tokens.append("<tempo:Morning>")
    elif hour < 17:
        tokens.append("<tempo:Afternoon>")
    else:
        tokens.append("<tempo:Evening>")

    # Duration
    duration = end - start
    minutes = int(duration.total_seconds() / 60)
    tokens.append(f"<tempo:duration-{minutes}min>")

    # Recurrence heuristic
    if re.search(r'weekly|daily|monthly', event.name or '', re.IGNORECASE):
        recurrence = re.search(r'weekly|daily|monthly', event.name, re.IGNORECASE).group().lower()
        tokens.append(f"<tempo:recurring-{recurrence}>")

    # Task type tag from summary
    summary = (event.name or '').lower()
    if "meeting" in summary:
        tokens.append("<tempo:meeting>")
    elif "handoff" in summary:
        tokens.append("<tempo:handoff>")
    elif "shipment" in summary:
        tokens.append("<tempo:shipment>")
    elif "review" in summary:
        tokens.append("<tempo:review>")
    elif "deadline" in summary:
        tokens.append("<tempo:deadline>")

    return tokens

# === Natural Language Context Generator === #
def event_to_context_sentence(event):
    start = event.begin.datetime.strftime("%I:%M %p").lstrip("0")
    title = event.name or "Untitled Event"
    desc = (event.description or "").strip()
    return f"At {start}, the user has an event titled '{title}'. {desc}"

# === System Prompt Builder === #
def generate_system_prompt_from_ics(ics_path: Path) -> str:
    with open(ics_path, 'r') as f:
        calendar = Calendar(f.read())

    prompt_blocks = []
    for event in sorted(calendar.events, key=lambda e: e.begin):
        tokens = generate_tempo_tokens(event)
        sentence = event_to_context_sentence(event)
        block = f"Event: {event.name}\nTokens: {' '.join(tokens)}\nSummary: {sentence}"
        prompt_blocks.append(block)

    header = "You are a planning assistant grounded in calendar context. Use the tempo tokens and descriptions to reason about task timing, urgency, and coordination."
    return header + "\n\n---\n" + "\n\n---\n".join(prompt_blocks)

# === CLI Entry === #
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate tempo-token prompt from .ics file")
    parser.add_argument("--ics", type=str, required=True, help="Path to .ics file")
    parser.add_argument("--output", type=str, help="Optional path to save prompt as .txt")
    args = parser.parse_args()

    ics_path = Path(args.ics)
    prompt = generate_system_prompt_from_ics(ics_path)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(prompt)
        print(f"✅ Prompt written to {args.output}")
    else:
        print(prompt)
