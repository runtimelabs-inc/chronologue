import asyncio
from mcp.server.stdio import stdio_server
from modules.sync_google_ics import authenticate_google, parse_ics_and_sync
from modules.embeddings import get_openai_embedding
from pathlib import Path

class MemorySyncServer(Server):
    def __init__(self):
        super().__init__()
        self.google_service = authenticate_google()

    async def list_tools(self):
        return [
            Tool(
                name="sync_to_google_calendar",
                description="Sync memory traces to Google Calendar",
                input_schema={"type": "string", "description": "Path to the memory JSON file"}
            ),
            Tool(
                name="generate_embedding",
                description="Generate OpenAI embeddings for a given text",
                input_schema={"type": "string", "description": "Text to generate embeddings for"}
            )
        ]

    async def call_tool(self, tool_name, tool_args):
        if tool_name == " parse_ics_and_sync":
            memory_json_path = Path(tool_args)
            if not memory_json_path.exists():
                return {"error": f"File not found: {memory_json_path}"}
            sync_memory_file_to_google_calendar(self.google_service, memory_json_path)
            return {"status": "success", "message": f"Synced memory traces from {memory_json_path.name}"}

        elif tool_name == "generate_embedding":
            text = tool_args
            embedding = get_openai_embedding(text)
            return {"embedding": embedding}

        else:
            return {"error": f"Unknown tool: {tool_name}"}

async def main():
    server = MemorySyncServer()
    await stdio_server(server)

if __name__ == "__main__":
    asyncio.run(main())


# 