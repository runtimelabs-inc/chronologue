import openai
import json
import time
from datetime import datetime

# Load your OpenAI API key
openai.api_key = "your-api-key-here"

# Load test suite
with open("chronologue_test_suite.json") as f:
    test_cases = json.load(f)

# Define the function specifications
function_definitions = [
    {
        "name": "schedule_event",
        "description": "Schedule a new calendar event.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "start_time": {"type": "string", "format": "date-time"},
                "duration_minutes": {"type": "integer"},
                "location": {"type": "string"},
                "description": {"type": "string"}
            },
            "required": ["title", "start_time", "duration_minutes"]
        }
    },
    {
        "name": "edit_event",
        "description": "Edit an existing event with updated fields.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "fields_to_update": {
                    "type": "object",
                    "additionalProperties": True
                }
            },
            "required": ["title", "fields_to_update"]
        }
    },
    {
        "name": "cancel_event",
        "description": "Cancel a scheduled calendar event.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"}
            },
            "required": ["title"]
        }
    }
]

def run_test(prompt, expected):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "user", "content": prompt}],
            functions=function_definitions,
            function_call="auto"
        )

        fc = response["choices"][0]["message"]["function_call"]
        name = fc["name"]
        arguments = json.loads(fc["arguments"])

        # Compare function name and arguments
        expected_name = expected["name"]
        expected_args = expected["arguments"]

        name_match = name == expected_name
        arg_match = arguments == expected_args

        if name_match and arg_match:
            return True, ""
        else:
            return False, f"\nPrompt: {prompt}\nExpected: {expected}\nGot: {{'name': {name}, 'arguments': {arguments}}}"
    except Exception as e:
        return False, f"Error running test for prompt: {prompt}\n{str(e)}"

# Run tests
results = []
for idx, case in enumerate(test_cases):
    passed, message = run_test(case["input_prompt"], case["expected_function_call"])
    results.append((idx, passed, message))
    time.sleep(1.2)  # Avoid hitting rate limits

# Summary
passed_count = sum(1 for _, passed, _ in results if passed)
total = len(results)
print(f"\n✅ {passed_count}/{total} tests passed.\n")

for idx, passed, message in results:
    if not passed:
        print(f"❌ Test {idx + 1} failed:{message}\n")
