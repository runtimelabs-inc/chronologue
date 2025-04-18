import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Union
from embeddings import embed_trace
from dotenv import load_dotenv
from openai import OpenAI
from openTSNE import TSNE
import matplotlib.pyplot as plt
import faiss

# Load environment variables for OpenAI
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a, b = np.array(vec1), np.array(vec2)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def load_embedded_traces(file_path: Path) -> List[Dict]:
    """Load memory traces with embeddings from a JSON file."""
    with open(file_path, "r") as f:
        traces = json.load(f)
    return [t for t in traces if "embedding" in t and len(t["embedding"]) == 1536]

def rank_traces_by_query(traces: List[Dict], query: str) -> List[Dict]:
    """Rank memory traces by similarity to a natural language query."""
    query_vec = embed_trace({"content": query})
    ranked = sorted(
        traces,
        key=lambda t: cosine_similarity(t["embedding"], query_vec),
        reverse=True
    )
    return ranked

def display_top_traces(traces: List[Dict], query: str, top_k: int = 5):
    """Print top-k most similar traces to a query."""
    print(f"\nTop {top_k} traces for query: '{query}'")
    query_vec = embed_trace({"content": query})
    for i, trace in enumerate(traces[:top_k]):
        score = cosine_similarity(trace["embedding"], query_vec)
        print(f"\nRank {i+1} – ID: {trace.get('id', 'unknown')}")
        print(f"Type: {trace.get('type', 'N/A')}")
        print(f"Timestamp: {trace.get('timestamp', 'N/A')}")
        print(f"Content: {trace.get('content', '')[:100]}")
        print(f"Similarity Score: {score:.4f}")



from openTSNE import TSNE
from openTSNE.affinity import PerplexityBasedNN
from openTSNE.initialization import pca

def visualize_traces_tsne_pytorch(traces: List[Dict]):
    embeddings = np.array([t["embedding"] for t in traces], dtype=np.float32)
    labels = [t.get("type", "unknown") for t in traces]

    affinities = PerplexityBasedNN(embeddings, perplexity=30, metric="cosine", method="annoy")
    init = pca(embeddings)

    tsne = TSNE(n_jobs=4, random_state=42)
    embedding = tsne.fit(embeddings, affinities=affinities, initialization=init)

    plt.figure(figsize=(10, 7))
    for label in set(labels):
        indices = [i for i, l in enumerate(labels) if l == label]
        plt.scatter(embedding[indices, 0], embedding[indices, 1], label=label, alpha=0.6)

    plt.title("t-SNE of Memory Traces")
    plt.xlabel("TSNE-1")
    plt.ylabel("TSNE-2")
    plt.legend()
    plt.tight_layout()
    plt.show()



def cluster_traces_faiss(traces: List[Dict], n_clusters: int = 5) -> List[Dict]:
    embeddings = np.array([t["embedding"] for t in traces], dtype='float32')
    kmeans = faiss.Kmeans(d=embeddings.shape[1], k=n_clusters, niter=20, verbose=False)
    kmeans.train(embeddings)
    distances, assignments = kmeans.index.search(embeddings, 1)

    for trace, label in zip(traces, assignments):
        trace["cluster"] = int(label[0])
    return traces



if __name__ == "__main__":
    
    # Use in demo to visualize traces
    
    data_dir = Path("/Users/derekrosenzweig/Documents/GitHub/chronologue/data/conversation/embedding")
    file_to_evaluate = data_dir / "lab_manager_2025_traces_embedded.json"  

    if not file_to_evaluate.exists():
        print(f"[!] File not found: {file_to_evaluate}")
        exit(1)

    traces = load_embedded_traces(file_to_evaluate)
    query = "Lab safety inspection and reagent restock"
    ranked_traces = rank_traces_by_query(traces, query)
    display_top_traces(ranked_traces, query, top_k=5)

    traces = load_embedded_traces(file_to_evaluate)
    traces = cluster_traces_faiss(traces, n_clusters=3)
    visualize_traces_tsne_pytorch(traces)