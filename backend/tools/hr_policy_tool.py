"""Tool: Search HR policy documents using a local vector store (RAG)."""

import os
import json
import hashlib
from pathlib import Path

from config import http_client, openai_client, MODEL

# Directory where HR policy PDFs/documents are stored
DOCUMENTS_DIR = Path("documents/hr_policies")

# Directory for the cached vector index
INDEX_DIR = Path("documents/hr_index")

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_hr_policy",
        "description": "Search the company HR policy documents for information. Use when the user asks about leave policy, attendance, benefits, code of conduct, appraisals, holidays, work from home, dress code, or any HR-related company policy.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The HR policy question or topic to search for, e.g. 'maternity leave policy', 'work from home rules', 'annual leave entitlement'.",
                }
            },
            "required": ["query"],
        },
    },
}

# --- In-memory vector store ---
_chunks = []  # List of {"text": ..., "embedding": ..., "source": ...}
_index_loaded = False


def _extract_text_from_pdf(filepath: Path) -> str:
    """Extract text from a PDF file."""
    import PyPDF2

    text = ""
    with open(filepath, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def _extract_text_from_txt(filepath: Path) -> str:
    """Extract text from a plain text or markdown file."""
    return filepath.read_text(encoding="utf-8", errors="ignore")


def _extract_text(filepath: Path) -> str:
    """Extract text from a document based on its extension."""
    ext = filepath.suffix.lower()
    if ext == ".pdf":
        return _extract_text_from_pdf(filepath)
    elif ext in (".txt", ".md", ".text"):
        return _extract_text_from_txt(filepath)
    elif ext == ".docx":
        import docx
        doc = docx.Document(str(filepath))
        return "\n".join(para.text for para in doc.paragraphs)
    else:
        return ""


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip())
    return chunks


def _get_embedding(text: str) -> list[float]:
    """Get embedding from OpenAI."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _get_index_hash() -> str:
    """Generate a hash of all document files to detect changes."""
    if not DOCUMENTS_DIR.exists():
        return ""
    files = sorted(DOCUMENTS_DIR.rglob("*"))
    hasher = hashlib.md5()
    for f in files:
        if f.is_file():
            hasher.update(str(f.relative_to(DOCUMENTS_DIR)).encode())
            hasher.update(str(f.stat().st_mtime).encode())
    return hasher.hexdigest()


def _save_index():
    """Save the vector index to disk for faster startup."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    data = [{"text": c["text"], "source": c["source"], "embedding": c["embedding"]} for c in _chunks]
    index_file = INDEX_DIR / "index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump({"hash": _get_index_hash(), "chunks": data}, f)


def _load_index() -> bool:
    """Try to load a cached index. Returns True if successful."""
    global _chunks
    index_file = INDEX_DIR / "index.json"
    if not index_file.exists():
        return False

    with open(index_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check if documents have changed
    if data.get("hash") != _get_index_hash():
        return False

    _chunks = data["chunks"]
    return True


def _build_index():
    """Read all documents, chunk them, compute embeddings, and build the index."""
    global _chunks, _index_loaded

    if _index_loaded:
        return

    # Try loading cached index first
    if _load_index():
        _index_loaded = True
        print(f"[HR Policy] Loaded cached index with {len(_chunks)} chunks.")
        return

    # Build fresh index
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    doc_files = [f for f in DOCUMENTS_DIR.rglob("*") if f.is_file() and f.suffix.lower() in (".pdf", ".docx", ".txt", ".md")] if DOCUMENTS_DIR.exists() else []

    if not doc_files:
        print("[HR Policy] No documents found in documents/hr_policies/")
        _index_loaded = True
        return

    print(f"[HR Policy] Indexing {len(doc_files)} documents...")

    _chunks = []
    for filepath in doc_files:
        text = _extract_text(filepath)
        if not text.strip():
            continue

        chunks = _chunk_text(text)
        for chunk in chunks:
            embedding = _get_embedding(chunk)
            _chunks.append({
                "text": chunk,
                "embedding": embedding,
                "source": filepath.name,
            })

    print(f"[HR Policy] Indexed {len(_chunks)} chunks from {len(doc_files)} documents.")

    # Cache the index
    if _chunks:
        _save_index()

    _index_loaded = True


def _clear_index():
    """Clear the cached index so it rebuilds on next query."""
    global _chunks, _index_loaded
    _chunks = []
    _index_loaded = False
    # Remove cached index file
    index_file = INDEX_DIR / "index.json"
    if index_file.exists():
        index_file.unlink()


def search_hr_policy(query: str) -> str:
    """Search HR policy documents for relevant information."""
    _build_index()

    if not _chunks:
        return "No HR policy documents have been uploaded yet. Please add PDF/DOCX/TXT files to the 'documents/hr_policies' folder."

    # Get query embedding
    query_embedding = _get_embedding(query)

    # Find top 5 most similar chunks
    scored = []
    for chunk in _chunks:
        score = _cosine_similarity(query_embedding, chunk["embedding"])
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_results = scored[:5]

    # Format results
    results = []
    for score, chunk in top_results:
        if score < 0.3:  # Skip low-relevance results
            continue
        results.append(f"[Source: {chunk['source']}] (relevance: {score:.2f})\n{chunk['text']}")

    if not results:
        return f"No relevant HR policy information found for: {query}"

    return "\n\n---\n\n".join(results)
