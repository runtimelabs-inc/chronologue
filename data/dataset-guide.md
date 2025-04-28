# Dataset Guide

This guide describes how to generate and structure a synthetic dataset for testing and developing memory traces, `.ics` calendar events, and integrated agent workflows.

---

## Goal

Produce a minimal, structured dataset consisting of:
- JSON memory traces with timestamps, task IDs, and types
- `.ics` files exportable/importable into calendar systems
- Model-compatible planning queries and structured outputs

---

## Step-by-Step Workflow

### 1. Define Your Schema

Each memory trace or event should follow a consistent schema:
```json
{
  "id": "m001",
  "type": "calendar_event",
  "title": "Project sync",
  "description": "Weekly status meeting on vLLM performance",
  "start": "2025-05-01T10:00:00Z",
  "end": "2025-05-01T10:30:00Z",
  "task_id": "vllm_tracking",
  "source": "synthetic"
}
```
This schema allows:
- Conversion into `.ics` via `export_ics.py`
- Use in memory-based inference loops
- Scheduling with the Google Calendar API via `scheduler.py`

---

### 2. Generate Traces Using GPT

#### Prompt Template:
> Simulate a week of memory traces for a lab manager overseeing a CRISPR experiment. Include a mix of `goal`, `observation`, `reflection`, and `calendar_event`. Provide each memory trace with an ISO 8601 timestamp, a task category, and a brief description. Format as a JSON array.

Save the output to:
```
data/user_sessions/lab_manager_crispr.json
```

---

### 3. Convert JSON to ICS

Start with model-generated memory traces in `.json` format and convert selected events to `.ics` files.

#### Steps:

1. **Generate or collect memory traces (JSON)**
   - Use `run_demo.py` or `scripts/generate_synthetic_dataset.py`
   - Save full sessions in `data/user_sessions/`

2. **Extract calendar events**
   - Filter memory traces by `"type": "calendar_event"`

3. **Export `.ics` files**
   - Use `export_ics.export_to_ics()` to write each event to:
```
data/calendar_exports/
```

4. **(Optional) Schedule with Google Calendar API**
   - Use `scheduler.create_event()` to post to a real calendar

5. **(Optional) Import `.ics` back for validation**
   - Use `import_ics.import_ics()` to parse and validate round-trip structure

---

## Example Dataset Structure

### JSON file:
```
data/user_sessions/lab_manager_april.json
```
- 3 sessions: `morning_planning`, `afternoon_sync`, `evening_reflection`
- 3–5 memory items per session
- Types: `goal`, `reflection`, `calendar_event`

### ICS file:
```
data/calendar_exports/lab_sync.ics
```
- 2–3 structured events with title, timestamp, and link

---

## Summary Table

| Component         | File                                | Tool              |
|------------------|-------------------------------------|-------------------|
| Memory traces    | `lab_manager.json`                  | `store.py`        |
| Calendar events  | `lab_manager.ics`                   | `export_ics.py`   |
| Model I/O test   | Prompt + response format            | `run_demo.py`     |
| Task scheduling  | `tasks.yaml` → calendar             | `scheduler.py`    |

---

## Next Steps
- Generate first trace with model 
- Convert into `.ics`
- Load into memory for retrieval testing
- Use CLI or API to simulate agent reasoning on top of synthetic memory



#### Convert json to ics 
```python 
from memory import store
from calendar import export_ics
import os

session = store.load_session("data/user_sessions/lab_manager.json")

for trace in session["memory"]:
    if trace["type"] == "calendar_event":
        filename = trace["title"].replace(" ", "_").lower() + ".ics"
        path = os.path.join("data/calendar_exports", filename)
        export_ics.export_to_ics(trace, path)
```

json vs txt 

```
Finalize README introduction at 8:30 AM as part of documentation task.
```

```json
{
  "type": "goal",
  "timestamp": "2025-04-10T08:30:00Z",
  "content": "Finalize README introduction",
  "task_id": "documentation"
}
```


With JSON, you can: 

- Sort, filter, group by `type`, `task_id`, `timestamp` 
- Embed only the `content` field 
- Convert to `.ics with clear start/end times 
- Chain entries together by session or task 

Structured fields = machine-readable, composable, and queryable


**Better Retrieval and Reasoning** 

Embedding or querying raw `.txt` is noisy: 

- No task label = difficult to cluster 
- No type = can't separate forward `goal` vs backward `reflection` 
- No timestamp = no temporal conditioning or planning logic 


JSON will let you selectively embed and retrieve: 

- `goals` for planning 
- `reflections` for review and reminders 
- `events` for calendar visualization and event summary 


```json 
{
  "id": "m102",
  "type": "reflection",
  "timestamp": "2025-04-10T18:45:00Z",
  "content": "Was distracted during kernel testing—need to mute Slack next time.",
  "task_id": "cutlass_perf_eval",
  "session_id": "2025-04-10-evening",
  "importance": 0.8,
  "completion_status": "done",
  "tags": ["focus", "experiment", "cutlass"],
  "source": "manual",
  "embedding": null
}

```




Outlining additional metadata parameters that can be added to structured memory traces in `.json` format. These fields enhance reasoning, retrieval, interface rendering, calendar linking, and long-term trace management.

---

## Core Fields (Required for Reasoning)
| Field       | Type     | Purpose                                             |
|-------------|----------|-----------------------------------------------------|
| `id`        | `str`    | Unique memory trace identifier                     |
| `type`      | `str`    | One of: `goal`, `observation`, `reflection`, `calendar_event` |
| `timestamp` | `str`    | ISO 8601 timestamp of memory trace                |
| `content`   | `str`    | Natural language statement or description         |
| `task_id`   | `str`    | High-level task category (e.g., `cutlass_docs`)    |

---

## Extended Metadata Fields

| Field               | Type              | Purpose                                                                 |
|--------------------|-------------------|-------------------------------------------------------------------------|
| `session_id`        | `str`             | Logical grouping of traces (e.g., `2025-04-10-AM-planning`)             |
| `user_id`           | `str`             | Supports multi-user memory systems                                      |
| `importance`        | `float` (0.0–1.0) | Priority for retrieval and reflection                                  |
| `duration_min`      | `int`             | Estimated or actual duration in minutes                                |
| `completion_status` | `str`             | One of: `pending`, `in_progress`, `done`, `canceled`                    |
| `tags`              | `List[str]`       | Semantic labels (e.g., `['focus', 'calendar', 'research']`)            |
| `source`            | `str`             | Origin of trace (e.g., `gpt_generated`, `manual`, `calendar_api`)      |
| `confidence`        | `float`           | Used with model-generated content for scoring or eval                  |
| `linked_event_uid`  | `str`             | Syncs with `.ics` UID or Google Calendar ID                            |
| `parent_task_id`    | `str`             | Links sub-tasks or reflections to a larger objective                   |
| `embedding`         | `List[float]` or `None` | Cached vector or embedding reference for retrieval                 |

---

## Example Trace with Metadata
```json
{
  "id": "m102",
  "type": "reflection",
  "timestamp": "2025-04-10T18:45:00Z",
  "content": "Was distracted during kernel testing—need to mute Slack next time.",
  "task_id": "cutlass_perf_eval",
  "session_id": "2025-04-10-evening",
  "importance": 0.8,
  "completion_status": "done",
  "tags": ["focus", "experiment", "cutlass"],
  "source": "manual",
  "collaborators": ["derek.rosenzweig1@gmail.com"],
  "embedding": null,
  "visibility": "private",
  "location": "Ace Hotel (NYC)" 
}
```

---

## Usage
These fields are used for:
- Trace filtering, sorting, and scoring during retrieval
- Calendar export or sync (e.g., `linked_event_uid`)
- ReAct agent input (e.g., inject only `goal` or `reflection` with high `importance`)
- Evaluation and clustering (e.g., `tags`, `task_id`, `session_id`)

They can be extended or versioned as the memory system evolves.

---

## Next Steps
- Define these in `memory/schema.py`
- Validate all traces prior to embedding or scheduling
- Log structured metadata alongside inference traces



***

**Testing Workflow** 

- Validate schema	Run schema.validate_memory_trace() on all traces	schema.py
- Embed memory	Use embed_memory_traces()	embedding.py
- Rank top traces	Use rank_traces()	trace_ranker.py
- Evaluate usage	Use summarize_impact_metrics()	impact_metrics.py
- Schedule or export	Use .ics or Google Calendar API	export_ics.py, scheduler.py


#### Dataset Curation 

