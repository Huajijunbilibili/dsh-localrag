"""localrag-mcp: local document RAG retrieval exposed as an MCP stdio server.

Tools exposed to the agent (via DSH's @deepseek-ai/dsh-mcp-client):
  - index_documents(path): index all .md/.txt files under a directory
  - search(query, k): semantic search with source citations
  - list_documents(): unique sources in the knowledge base

Stack: MCP (FastMCP) + Chroma (persistent) + fastembed (BAAI/bge-small-zh-v1.5, ONNX, offline after first download).
Requires Python 3.10+.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb
from fastembed import TextEmbedding
from mcp.server.fastmcp import FastMCP

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
SUPPORTED_SUFFIXES = {".md", ".txt"}

mcp = FastMCP("localrag")

_embedding: TextEmbedding | None = None


def get_embedding() -> TextEmbedding:
    """Lazy singleton; the ONNX model downloads on first use (~95MB for bge-small-zh)."""
    global _embedding
    if _embedding is None:
        _embedding = TextEmbedding(model_name="BAAI/bge-small-zh-v1.5")
    return _embedding


def get_collection():
    client = chromadb.PersistentClient(path=str(DATA_DIR / "chroma"))
    return client.get_or_create_collection("documents")


def chunk_text(text: str) -> list[str]:
    """Sliding-window chunking (chars) with overlap; no heavy deps in v1."""
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + CHUNK_SIZE, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = end - CHUNK_OVERLAP
    return chunks


@mcp.tool()
def index_documents(path: str) -> str:
    """Index all .md/.txt files under PATH into the local knowledge base. Returns a summary."""
    root = Path(path).resolve()
    if not root.is_dir():
        return f"error: {path} is not a directory"
    files = sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    )
    if not files:
        return f"no .md/.txt files found under {root}"
    emb = get_embedding()
    col = get_collection()
    total = 0
    indexed = 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        chunks = chunk_text(text)
        if not chunks:
            continue
        vectors = list(emb.embed(chunks))
        ids = [f"{f.stem}-{i}" for i in range(len(chunks))]
        metadatas = [{"source": str(f), "chunk": i} for i in range(len(chunks))]
        col.upsert(ids=ids, embeddings=vectors, documents=chunks, metadatas=metadatas)
        total += len(chunks)
        indexed += 1
    return f"indexed {indexed} files, {total} chunks into '{col.name}' (data dir: {DATA_DIR})"


@mcp.tool()
def search(query: str, k: int = 5) -> list[dict[str, Any]]:
    """Semantic search the local knowledge base; returns top-k chunks with source paths and scores."""
    emb = get_embedding()
    col = get_collection()
    if col.count() == 0:
        return [{"error": "knowledge base is empty; call index_documents first"}]
    vector = list(emb.embed([query]))[0]
    n = min(max(1, k), col.count())
    res = col.query(
        query_embeddings=[vector],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )
    out: list[dict[str, Any]] = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        out.append(
            {
                "text": doc,
                "source": meta.get("source"),
                "chunk": meta.get("chunk"),
                "score": round(1.0 - dist, 4),
            }
        )
    return out


@mcp.tool()
def list_documents() -> list[str]:
    """List all source documents currently in the knowledge base."""
    col = get_collection()
    metas = col.get(include=["metadatas"])["metadatas"]
    return sorted({m.get("source") for m in metas if m})


if __name__ == "__main__":
    mcp.run(transport="stdio")
