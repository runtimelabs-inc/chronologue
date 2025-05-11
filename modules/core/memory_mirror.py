# modules/core/memory_mirror.py (Structured Output Version, OpenAI >= 1.0)

import os
import json
from datetime import datetime
from typing import List, Optional
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Pydantic Models ---
class Reflection(BaseModel):
    type: str = "reflection"
    timestamp: str
    content: str
    linked_task_id: str
    feedback_score: float = Field(..., ge=-1.0, le=1.0)

class MemoryTrace(BaseModel):
    type: str
    timestamp: str
    content: str
    task_id: Optional[str] = None
    importance: Optional[float] = None


# --- Sample Data Loader ---
def load_sample_memory_traces() -> List[MemoryTrace]:
    return [MemoryTrace(**trace) for trace in [
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
    ]]


# --- Trace Comparison Engine ---
def compare_traces(planned_trace: MemoryTrace, executed_trace: Optional[MemoryTrace]) -> dict:
    divergences = {}
    if not executed_trace:
        divergences['status'] = 'not_started'
    elif planned_trace.content != executed_trace.content:
        divergences['content_mismatch'] = True
    # Add more divergence checks as needed
    return divergences

# --- Mirror Reflection Generator ---
def generate_reflection(planned_trace: MemoryTrace, divergences: dict) -> Optional[Reflection]:
    prompt = (
        "You are a critical productivity coach. Evaluate the following task:\n\n"
        f"Goal: {planned_trace.content}\n"
        f"Divergences: {json.dumps(divergences)}\n\n"
        "Provide a reflection in JSON format."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You respond only in structured JSON following the schema."},
                {"role": "user", "content": prompt}
            ],
            response_format="json"
        )
        raw_json = response.choices[0].message.content
        reflection = Reflection.model_validate_json(raw_json)
        return reflection
    except Exception as e:
        print(f"[ERROR] Failed to generate reflection: {e}")
        return None

# --- Personal Scorecard ---
def generate_scorecard(reflections: List[Reflection]) -> dict:
    scorecard = {
        "goals_completed": sum(1 for r in reflections if r.feedback_score > 0),
        "average_deviation": sum(r.feedback_score for r in reflections) / len(reflections) if reflections else 0,
        "top_positive": sorted(reflections, key=lambda r: r.feedback_score, reverse=True)[:3],
        "top_failures": sorted(reflections, key=lambda r: r.feedback_score)[:3]
    }
    return scorecard

# --- Main Flow ---
def main():
    # Load sample data
    traces = load_sample_memory_traces()

    # Compare traces and generate reflections
    reflections = []
    for planned_trace in traces:
        executed_trace = None  # Placeholder for actual executed trace retrieval
        divergences = compare_traces(planned_trace, executed_trace)
        reflection = generate_reflection(planned_trace, divergences)
        if reflection:
            reflections.append(reflection)

    # Generate and print scorecard
    scorecard = generate_scorecard(reflections)
    print(json.dumps(scorecard, indent=2))

if __name__ == "__main__":
    main()






# from openai import OpenAI
# from pydantic import BaseModel, Field
# from typing import List, Optional
# from datetime import datetime
# import json
# import os
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # Initialize OpenAI client
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




# # Print the response
# print(response.choices[0].message["content"])

# print("🚀 Memory Mirror: Structured Output Mode")

# # --- Pydantic Models ---
# class Reflection(BaseModel):
#     type: str = "reflection"
#     timestamp: str
#     content: str
#     linked_task_id: str
#     feedback_score: float = Field(..., ge=-1.0, le=1.0)

# class MemoryTrace(BaseModel):
#     type: str
#     timestamp: str
#     content: str
#     task_id: Optional[str] = None
#     importance: Optional[float] = None


# # --- Sample Data Loader ---
# def load_sample_memory_traces() -> List[MemoryTrace]:
#     return [MemoryTrace(**trace) for trace in [
#         {
#             "type": "goal",
#             "timestamp": "2025-05-09T08:00:00",
#             "content": "Write introduction for the Chronologue README",
#             "task_id": "task-001",
#             "importance": 0.9
#         },
#         {
#             "type": "goal",
#             "timestamp": "2025-05-09T09:00:00",
#             "content": "Push mirror_agent.py to GitHub",
#             "task_id": "task-002",
#             "importance": 0.7
#         },
#         {
#             "type": "goal",
#             "timestamp": "2025-05-09T10:00:00",
#             "content": "Go for a 30-minute run",
#             "task_id": "task-003",
#             "importance": 0.5
#         },
#         {
#             "type": "observation",
#             "timestamp": "2025-05-09T10:30:00",
#             "content": "Completed 30-minute run at Golden Gate Park",
#             "task_id": "task-003"
#         },
#         {
#             "type": "observation",
#             "timestamp": "2025-05-09T08:45:00",
#             "content": "Wrote and edited the introduction section of the Chronologue README",
#             "task_id": "task-001"
#         }
#     ]]


# # --- Core Logic ---
# def match_goal_to_observation(goals: List[MemoryTrace], observations: List[MemoryTrace]):
#     matches = []
#     for goal in goals:
#         obs = next((o for o in observations if o.task_id == goal.task_id), None)
#         matches.append({"goal": goal, "observation": obs})
#     return matches


# def generate_reflection(goal: MemoryTrace, observation: Optional[MemoryTrace]) -> Optional[Reflection]:
#     prompt = (
#         "You are a critical productivity coach. Your job is to evaluate whether the user's stated goal was completed.\n\n"
#         f"Goal: {goal.content}\n"
#         f"Observation: {observation.content if observation else 'No observation recorded.'}\n\n"
#         "Respond in JSON format with the following keys:\n"
#         "- type: always 'reflection'\n"
#         "- timestamp: current timestamp\n"
#         "- content: 1-2 sentence evaluation of follow-through\n"
#         "- linked_task_id: ID of the goal\n"
#         "- feedback_score: float between -1.0 and 1.0\n"
#     )

#     try:
#         response = client.chat.completions.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": "You respond only in structured JSON following the schema."},
#                 {"role": "user", "content": prompt}
#             ],
#             response_format="json"
#         )
#         raw_json = response.choices[0].message.content
#         reflection = Reflection.model_validate_json(raw_json)
#         return reflection
#     except Exception as e:
#         print(f"[ERROR] Failed to generate reflection for {goal.task_id}: {e}")
#         return None


# # --- Main Flow ---
# def main():
#     traces = load_sample_memory_traces()
#     goals = [t for t in traces if t.type == "goal"]
#     observations = [t for t in traces if t.type == "observation"]

#     print(f"→ Found {len(goals)} goals and {len(observations)} observations.")
#     matches = match_goal_to_observation(goals, observations)

#     reflections = []
#     for pair in matches:
#         goal, obs = pair["goal"], pair["observation"]
#         print(f"🧠 Reflecting on goal: {goal.task_id}")
#         reflection = generate_reflection(goal, obs)
#         if reflection:
#             reflections.append(reflection)
#             print(f"✅ {reflection.feedback_score:.1f} — {reflection.content}\n")
#         else:
#             print("⚠️ Reflection generation failed.\n")

#     # Output result
#     output_path = "reflections_output.json"
#     with open(output_path, "w") as f:
#         json.dump([r.dict() for r in reflections], f, indent=2)
#     print(f"\n📁 Saved {len(reflections)} reflections to {output_path}")


# if __name__ == "__main__":
#     main()
