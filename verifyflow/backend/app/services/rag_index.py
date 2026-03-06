from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions  # type: ignore
import os
from typing import List, Dict

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

chroma_client = chromadb.PersistentClient(path="./chroma_data")


def get_or_create_collection(session_id: int):
    collection_name = f"session_{session_id}"
    try:
        collection = chroma_client.get_collection(name=collection_name)
    except:
        collection = chroma_client.create_collection(
            name=collection_name,
            embedding_function=None
        )
    return collection


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 100) -> List[str]:
    """Simple overlapping chunker"""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = end - overlap
        if start >= len(text):
            break
    return chunks


def batch_embeddings(chunks: List[str], batch_size: int = 50) -> List:
    """Generate embeddings in batches to avoid memory issues"""
    all_embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        response = client.embeddings.create(
            input=batch,
            model="text-embedding-3-small"
        )
        all_embeddings.extend([item.embedding for item in response.data])
    return all_embeddings


def index_references_for_session(
    session_id: int,
    references: List[Dict]
):
    collection = get_or_create_collection(session_id)

    all_chunks = []
    all_metadatas = []
    all_ids = []

    for ref in references:
        if not ref.get("parsed_text"):
            continue
        chunks = chunk_text(ref["parsed_text"])
        for i, chunk in enumerate(chunks):
            chunk_id = f"ref_{ref['id']}_chunk_{i}"
            all_chunks.append(chunk)
            all_metadatas.append({
                "filename": ref["filename"],
                "reference_id": ref["id"],
                "chunk_index": i,
                "source": f"{ref['filename']} (chunk {i+1})"
            })
            all_ids.append(chunk_id)

    if not all_chunks:
        return {"status": "no content to index"}

    embeddings = batch_embeddings(all_chunks)

    collection.add(
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadatas,
        ids=all_ids
    )

    return {
        "status": "success",
        "chunk_count": len(all_chunks),
        "collection_name": collection.name
    }