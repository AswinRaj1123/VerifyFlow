import chromadb
from openai import OpenAI
import json

client = OpenAI()
chroma_client = chromadb.PersistentClient(path="./chroma_db")

def get_collection(session_id: int):
    return chroma_client.get_or_create_collection(name=f"session_{session_id}")

# add references (called after upload)
def index_references(session_id: int, docs: list):
    collection = get_collection(session_id)
    for doc in docs:
        chunks = [doc["parsed_text"][i:i+1000] for i in range(0, len(doc["parsed_text"]), 800)]
        for i, chunk in enumerate(chunks):
            emb = client.embeddings.create(input=chunk, model="text-embedding-3-small").data[0].embedding
            collection.add(
                documents=[chunk],
                embeddings=[emb],
                metadatas=[{"filename": doc["filename"], "chunk": i}],
                ids=[f"{doc['filename']}_{i}"]
            )

# main generate function (used for full + partial)
def generate_answers(session_id: int, question_texts: list[str], existing_questions=None):
    collection = get_collection(session_id)
    results = []

    for q_text in question_texts:
        q_emb = client.embeddings.create(input=q_text, model="text-embedding-3-small").data[0].embedding
        res = collection.query(query_embeddings=[q_emb], n_results=5, include=["documents", "metadatas", "distances"])

        context = "\n\n".join([f"Source: {m['filename']}\n{d}" for d, m in zip(res["documents"][0], res["metadatas"][0])])
        avg_dist = sum(res["distances"][0]) / len(res["distances"][0]) if res["distances"][0] else 2.0
        confidence = max(0, int(100 * (1 - avg_dist / 2)))   # cosine normalized

        if confidence < 20 or not context:
            answer = "Not found in references."
            citations = []
        else:
            prompt = f"""Answer ONLY using the context below. If insufficient, say exactly "Not found in references."
Question: {q_text}

Context:
{context}

Return JSON: {{"answer": "...", "citations": ["document name - section"]}}"""

            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(resp.choices[0].message.content)
            answer = data["answer"]
            citations = data["citations"]

        results.append({
            "question": q_text,
            "answer": answer,
            "citations": citations,
            "confidence": confidence
        })
    return results