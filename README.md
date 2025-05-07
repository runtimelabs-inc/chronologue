# Chronologue: Calendar-Grounded Memory and Agent Interface 

[![Google Calendar API](https://img.shields.io/badge/Google%20Calendar-API%20Integration-green)](https://developers.google.com/calendar)
[![iCalendar](https://img.shields.io/badge/iCalendar-Compatible-blue)](https://datatracker.ietf.org/doc/html/rfc5545)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![MCP Protocol](https://img.shields.io/badge/Model%20Context%20Protocol-Supported-purple)](https://github.com/modelcontextprotocol)

## Overview

Chronologue transforms memory—such as conversation history—into calendar-grounded interfaces for agents and users. By bridging natural language, structured memory, and scheduling, it enables agents to operate over time while giving users a familiar, editable interface to steer behavior and planning.

Chronologue connects language models to calendar APIs, enabling agents to generate, update, and retrieve events from natural language prompts. This bidirectional loop grounds agent reasoning in time, allowing both users and models to plan, recall, and adapt with transparency and continuity

> *“We make ourselves intelligent by designing environments that contain relevant information and make it accessible to our future selves.”*  
> — [Donald Norman](https://jnd.org/)
>
> *“Memory systems grounded in user context condition the future distribution of responses that a language model will sample from.”*
>
> *“Time is a core substrate for intelligent behavior.”*


## Getting Started 


### Install `uv`


```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Clone and Setup 

```bash
git clone https://github.com/dr2633/Chronologue.git
cd chronologue
uv init
uv venv
source .venv/bin/activate
```

## Install Dependencies 

```bash
uv pip install -r requirements.txt
uv add "mcp[cli]" httpx
```

If developing in MCP locally: 

```bash
brew install node
```

## Set Up Environment 

Add .env and set your API keys and Google Workspace credentials: 

```
OPENAI_API_KEY=your-openai-key
CLAUDE_API_KEY=your-anthropic-key
GEMINI_API_KEY=your-gemini-key
GOOGLE_CLIENT_CREDENTIALS=calendar/credentials.json
GOOGLE_TOKEN_FILE=calendar/token.json
```

Follow the [Google Calendar API setup guide](calendar/google_API_setup.md) to enable calendar sync.

## Core Scripts 

### JSON ↔ ICS Conversion

```bash
python modules/export_calendar.py        # JSON → ICS
python modules/import_calendar.py        # ICS → JSON
python modules/embeddings.py        # Generate embeddings for retrieval
```

#### Run MCP Server 

```bash
mcp dev mcp/server-verifier.py
mcp dev mcp/server_calendar.py
mcp dev mcp/server_google_calendar.py
```

#### Streamlit Chat Editor Interface 

```bash
streamlit run modules/streamlit_chat_editor.py
```


### Sample Workflow 

Model Output → `.ics` Calendar Format

```json
{
  "title": "Project Sync: Inference Pipeline",
  "description": "Check progress on GPU inference benchmarks.",
  "start": "2025-04-11T14:00:00Z",
  "end": "2025-04-11T14:30:00Z",
  "location": "https://zoom.us/my/benchmark-sync",
  "organizer_email": "agent@memorysystem.ai"
}
```

Becomes `.ics` file: 

```
BEGIN:VEVENT
DTSTART:20250411T140000Z
DTEND:20250411T143000Z
SUMMARY:Project Sync: Inference Pipeline
DESCRIPTION:Check progress on GPU inference benchmarks.
LOCATION:https://zoom.us/my/benchmark-sync
UID:project-sync-20250411@memorysystem.ai
DTSTAMP:20250410T230000Z
ORGANIZER;CN=Memory Agent:mailto:agent@memorysystem.ai
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT
```

## Contact 

For demos, collaboration, or integration questions:  
**Derek Rosenzweig**  
derek.rosenzweig1@gmail.com  
[github.com/dr2633](https://github.com/dr2633)
## License

Chronologue is open-source under the [Apache 2.0 License](https://opensource.org/licenses/Apache-2.0).
