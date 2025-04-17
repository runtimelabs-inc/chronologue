import os
import json
from pathlib import Path
from typing import List, Dict, Union
from dotenv import load_dotenv
from openai import OpenAI

# Load API key from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_openai_embedding(text: str) -> List[float]:
    try:
        response = client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"[Embedding Error] {e}")
        return []

def embed_trace(trace: Dict[str, Union[str, List[float]]]) -> List[float]:
    return get_openai_embedding(trace.get("content", ""))

def embed_memory_traces(traces: List[Dict], overwrite: bool = False) -> List[Dict]:
    for trace in traces:
        if overwrite or "embedding" not in trace or not trace["embedding"]:
            trace["embedding"] = embed_trace(trace)
    return traces
if __name__ == "__main__":
    # Make script location robust
    data_dir = '/Users/derekrosenzweig/Documents/GitHub/mmcr-memory-system/data'
    input_dir = Path(f"{data_dir}/conversation/raw/")
    output_dir = Path(f"{data_dir}/conversation/embedding/")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Iterate over all JSON files in the input directory
    for input_file in input_dir.glob("*.json"):
        output_path = output_dir / f"{input_file.stem}_embedded.json"

        if input_file.exists():
            with open(input_file, "r") as f:
                session_data = json.load(f)

            memory = session_data.get("memory", [])
            embedded = embed_memory_traces(memory)

            for trace in embedded[:2]:
                print(trace.get("id", "no-id"), "→", trace.get("embedding", [])[:5])
                print("Embedding length:", len(trace.get("embedding", [])))
            
            valid = [t for t in embedded if "embedding" in t and len(t["embedding"]) == 1536]
            print(f"[✓] Embedded {len(valid)} of {len(embedded)} traces successfully.")

            with open(output_path, "w") as f:
                json.dump(embedded, f, indent=2)

            print(f"[✓] Saved to {output_path.resolve()}")
        else:
            print(f"[Error] File not found: {input_file.resolve()}")

# # Vector embeddings: https://platform.openai.com/docs/guides/embeddings 
