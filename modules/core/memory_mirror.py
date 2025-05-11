# python modules/core/memory_mirror.py
# python /Users/derekrosenzweig/Documents/GitHub/chronologue/modules/core/memory_mirror.py

import json
import os
from datetime import datetime
from typing import List, Dict, Optional

import openai


print("🚀 Script started")

# --- Environment Setup ---
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise EnvironmentError("OPENAI_API_KEY not found. Set it in your environment variables.")

MemoryTrace = Dict[str, any]


# --- Sample Data ---
def load_sample_memory_traces() -> List[MemoryTrace]:
    return [
        {
            "type": "goal",
            "timestamp": "2025-05-09T08:00:00",
            "content": "Write introduction for the Chronologue README",
            "task_id": "task-001",
            "importance": 0.9
        },
        {
            "type": "goal",
            "timestamp": "2025-05-09T09:00:00",
            "content": "Push mirror_agent.py to GitHub",
            "task_id": "task-002",
            "importance": 0.7
        },
        {
            "type": "goal",
            "timestamp": "2025-05-09T10:00:00",
            "content": "Go for a 30-minute run",
            "task_id": "task-003",
            "importance": 0.5
        },
        {
            "type": "observation",
            "timestamp": "2025-05-09T10:30:00",
            "content": "Completed 30-minute run at Golden Gate Park",
            "task_id": "task-003"
        },
        {
            "type": "observation",
            "timestamp": "2025-05-09T08:45:00",
            "content": "Wrote and edited the introduction section of the Chronologue README",
            "task_id": "task-001"
        }
    ]


# --- Core Functions ---
def filter_traces_by_type(traces: List[MemoryTrace], trace_type: str) -> List[MemoryTrace]:
    return [trace for trace in traces if trace.get("type") == trace_type]


def match_goal_to_observation(goals: List[MemoryTrace], observations: List[MemoryTrace]) -> List[Dict[str, any]]:
    matches = []
    for goal in goals:
        task_id = goal.get("task_id")
        matched_obs = next((obs for obs in observations if obs.get("task_id") == task_id), None)
        match_status = "matched" if matched_obs else "unfulfilled"
        matches.append({
            "goal": goal,
            "observation": matched_obs,
            "match_status": match_status
        })
    return matches


def generate_reflection_with_llm(goal: Dict, observation: Optional[Dict]) -> Dict:
    goal_text = goal["content"]
    obs_text = observation["content"] if observation else "No observation recorded."

    prompt = (
        f"You are a critical productivity coach. Evaluate the following task:\n\n"
        f"Goal: {goal_text}\n"
        f"Observation: {obs_text}\n\n"
        f"Provide clear, direct feedback to the user on whether they followed through on their stated intention. "
        f"Then assign a feedback_score from -1.0 (not completed) to 1.0 (fully completed)."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        content = response.choices[0].message["content"].strip()
    except Exception as e:
        content = f"[ERROR] OpenAI API call failed: {str(e)}"

    return {
        "type": "reflection",
        "timestamp": datetime.now().isoformat(),
        "content": content,
        "linked_task_id": goal.get("task_id"),
        "feedback_score": None
    }


def generate_reflections(matches: List[Dict[str, any]]) -> List[MemoryTrace]:
    reflections = []
    for match in matches:
        print(f"→ Processing goal: {match['goal']['content']}")
        if match["observation"]:
            print(f"✓ Matched with observation: {match['observation']['content']}")
        else:
            print("✗ No observation found.")
        reflection = generate_reflection_with_llm(match["goal"], match["observation"])
        print(f"Generated reflection: {reflection['content']}\n")
        reflections.append(reflection)
    return reflections


# --- Entrypoint ---
def main():
    print("📌 Loading memory traces...")
    traces = load_sample_memory_traces()
    goals = filter_traces_by_type(traces, "goal")
    observations = filter_traces_by_type(traces, "observation")

    print(f"→ Found {len(goals)} goals and {len(observations)} observations.")

    matches = match_goal_to_observation(goals, observations)
    reflections = generate_reflections(matches)

    print("\n=== FINAL REFLECTION OUTPUT ===")
    print(json.dumps(reflections, indent=2))


if __name__ == "__main__":
    main()
