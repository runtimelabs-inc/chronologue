# python modules/tempo/tempo_token.py

from ics import Calendar
from datetime import datetime
from openai import OpenAI
import re

client = OpenAI()

# --- Parse ICS and Generate Tempo Tokens ---
def parse_ics_to_events(ics_path):
    with open(ics_path, 'r') as f:
        calendar = Calendar(f.read())
    events = []
    for event in calendar.events:
        tokens = generate_tempo_tokens(event)
        events.append({
            "uid": event.uid,
            "title": event.name,
            "description": event.description or "",
            "start": event.begin.datetime,
            "end": event.end.datetime,
            "tokens": tokens
        })
    return events

# --- Tempo Token Generator ---
def generate_tempo_tokens(event):
    tokens = []
    start = event.begin.datetime
    end = event.end.datetime

    tokens.append(f"<tempo:uid-{event.uid}>")
    tokens.append(f"<tempo:{start.strftime('%Y-%m-%dT%H:%MZ')}>")
    tokens.append(f"<tempo:{start.strftime('%A')}>")

    hour = start.hour
    if hour < 12:
        tokens.append("<tempo:Morning>")
    elif hour < 17:
        tokens.append("<tempo:Afternoon>")
    else:
        tokens.append("<tempo:Evening>")

    duration = int((end - start).total_seconds() / 60)
    tokens.append(f"<tempo:duration-{duration}min>")

    if "meeting" in event.name.lower():
        tokens.append("<tempo:meeting>")
    if "urgent" in event.description.lower():
        tokens.append("<tempo:urgent>")

    return tokens

# --- Prompt Constructor ---
def construct_prompt(events, user_query, date_filter=None):
    prompt = "You are a calendar-aware assistant. Based on the user's schedule:\n"
    for e in events:
        if date_filter and e["start"].date().isoformat() != date_filter:
            continue
        token_str = " ".join(e["tokens"])
        time_str = e["start"].strftime("%I:%M %p").lstrip("0")
        prompt += f"- {e['title']} at {time_str}. {token_str}\n"
    prompt += f"\nUser prompt: {user_query}\n"
    return prompt

# --- Run Grounded Prompt ---
def run_grounded_prompt(prompt):
    res = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Answer the user query using the structured schedule."}
        ]
    )
    return res.choices[0].message.content.strip()

file = '/Users/derekrosenzweig/Documents/GitHub/chronologue/modules/tempo/example_schedule.ics'

# --- CLI Test Routine ---
def test_prompt_grounding():
    ics_path = file
    events = parse_ics_to_events(ics_path)

    prompt_tests = [
        {
            "user_query": "When should I schedule a haircut next Tuesday?",
            "date": "2025-05-13"
        },
        {
            "user_query": "Can I reschedule the lab meeting to later in the afternoon?",
            "date": "2025-05-14"
        },
        {
            "user_query": "Do I have any conflicts if I add a meeting at 3 PM Thursday?",
            "date": "2025-05-15"
        },
        {
            "user_query": "What free slots do I have on Friday morning?",
            "date": "2025-05-16"
        }
    ]

    for test in prompt_tests:
        print("\n==== User Query ====")
        print(test["user_query"])
        grounded_prompt = construct_prompt(events, test["user_query"], date_filter=test["date"])
        print("\n==== Grounded Prompt ====")
        print(grounded_prompt)
        response = run_grounded_prompt(grounded_prompt)
        print("\n==== Model Response ====")
        print(response)
        print("==========================\n")

if __name__ == "__main__":
    test_prompt_grounding()