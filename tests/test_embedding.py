# tests/test_embeddings.py
import os
from modules import embeddings
from unittest.mock import patch, MagicMock

def test_get_openai_embedding_success():
    sample_text = "This is a test sentence for embedding."
    with patch.object(embeddings.client.embeddings, 'create') as mock_create:
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.0] * 1536)]
        mock_create.return_value = mock_response

        embedding = embeddings.get_openai_embedding(sample_text)
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)


def test_get_openai_embedding_error():
    with patch.object(embeddings.client.embeddings, 'create', side_effect=Exception("API Error")):
        embedding = embeddings.get_openai_embedding("trigger error")
        assert embedding == []


def test_embed_trace_with_content():
    with patch("modules.embeddings.get_openai_embedding", return_value=[0.1] * 1536):
        trace = {"content": "Test content"}
        embedding = embeddings.embed_trace(trace)
        assert isinstance(embedding, list)
        assert len(embedding) == 1536


def test_embed_memory_traces_overwrite_false_skips_existing():
    with patch("modules.embeddings.get_openai_embedding", return_value=[0.1] * 1536):
        trace1 = {"content": "Pre-embedded", "embedding": [0.9] * 1536}
        trace2 = {"content": "Needs embedding"}
        traces = embeddings.embed_memory_traces([trace1, trace2], overwrite=False)
        assert traces[0]["embedding"] == [0.9] * 1536
        assert traces[1]["embedding"] == [0.1] * 1536


def test_embed_memory_traces_overwrite_true_embeds_all():
    with patch("modules.embeddings.get_openai_embedding", return_value=[0.5] * 1536):
        trace1 = {"content": "Embed me", "embedding": [0.9] * 1536}
        trace2 = {"content": "Embed me too"}
        traces = embeddings.embed_memory_traces([trace1, trace2], overwrite=True)
        for trace in traces:
            assert trace["embedding"] == [0.5] * 1536
