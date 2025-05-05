import json
from openai import OpenAI

client = OpenAI()

# Prompt to send to GPT-4.1
PROMPT = """Estimate how long it takes to grill a 1.5 lb skirt steak at 425°F. 
For each doneness level (rare, medium-rare, medium, well-done), provide:
- Mean cook time in minutes
- A 2-value range (min and max time in minutes)
- Recommended internal temperature in °F
- A brief note about cooking technique or doneness description

Respond in a JSON format with this structure:

{
  "task": "...",
  "doneness_profiles": {
    "rare": {
      "mean_minutes": ...,
      "range_minutes": [..., ...],
      "recommended_internal_temp_f": ...,
      "notes": "..."
    },
    ...
  }
}
"""

# Evaluation logic
def evaluate_distribution(output: dict) -> list[str]:
    errors = []
    levels = ["rare", "medium_rare", "medium", "well_done"]
    profiles = output.get("doneness_profiles", {})

    for level in levels:
        profile = profiles.get(level)
        if not profile:
            errors.append(f"Missing profile: {level}")
            continue
        try:
            mean = profile["mean_minutes"]
            r_min, r_max = profile["range_minutes"]
            if not (r_min <= mean <= r_max):
                errors.append(f"{level}: mean {mean} not in range {r_min}-{r_max}")
            if not isinstance(profile["recommended_internal_temp_f"], (int, float)):
                errors.append(f"{level}: missing or invalid internal temp")
            if "notes" not in profile or not profile["notes"].strip():
                errors.append(f"{level}: missing or empty notes")
        except Exception as e:
            errors.append(f"{level}: error parsing profile - {str(e)}")

    return errors if errors else ["PASS"]

# Send prompt and evaluate
def run_test():
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a cooking assistant."},
                {"role": "user", "content": PROMPT}
            ],
            temperature=0.7,
            max_tokens=500
        )

        raw_content = response.choices[0].message.content.strip()
        print("=== Raw Output ===")
        print(raw_content)

        # Parse JSON response from LLM
        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError:
            print("\n[!] Failed to parse response as JSON.")
            return

        print("\n=== Evaluation Result ===")
        results = evaluate_distribution(parsed)
        for line in results:
            print(line)

    except Exception as e:
        print(f"[!] OpenAI API error: {e}")

if __name__ == "__main__":
    run_test()
