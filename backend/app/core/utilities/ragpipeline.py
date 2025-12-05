import os
from pinecone import Pinecone
from huggingface_hub import InferenceClient
import requests
from sentence_transformers import SentenceTransformer

_embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

hf_token = os.getenv("HF_TOKEN", "")

client = InferenceClient(token=hf_token)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "") 
INDEX_NAME = "ai-mock-interview-questions"

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

def _normalize_for_filter(md: dict) -> dict:
    """Normalize values"""
    if md is None:
        return {}
    out = {}

    # Company: strip only (assumes you indexed proper case like 'Meta')
    if md.get("Company"):
        out["Company"] = str(md["Company"]).strip()

    # Role: title-case to match e.g. 'Data Scientist'
    if md.get("Role"):
        out["Role"] = str(md["Role"]).strip().title()

    # Round Number: ensure it starts with 'Round '
    rn = md.get("Round Number")
    if rn is not None and str(rn).strip() != "":
        rn_str = str(rn).strip()
        out["Round Number"] = rn_str if rn_str.lower().startswith("round") else f"Round {rn_str}"

    return out

def build_md(company: str | None, role: str | None, level: str | int | None) -> dict:
    md = {}

    if company:
        md["Company"] = str(company)

    if role:
        md["Role"] = str(role)

    # level appears to be "Round Number"
    if level:
        md["Round Number"] = str(level)

    return md


def run_full_pipeline(company, role, level):
    #user_query, metadata = extract_metadata_from_query()
    metadata = build_md(company, role, level)
    if metadata is None:
        metadata = {}

    # --- normalize BEFORE building the filter ---
    norm = _normalize_for_filter(metadata)

    # Defining metadata filter (same structure as your Chroma version)
    and_clauses = []
    if norm.get("Company"):
        and_clauses.append({"Company": {"$eq": norm["Company"]}})
    if norm.get("Role"):
        and_clauses.append({"Role": {"$eq": norm["Role"]}})
    if norm.get("Round Number"):
        and_clauses.append({"Round Number": {"$eq": norm["Round Number"]}})

    metadata_filter = {"$and": and_clauses} if and_clauses else None

    # Query string (use normalized values for consistency)
    role_for_query = (norm.get("Role") or metadata.get("Role") or "data science").strip()
    round_for_query = (norm.get("Round Number") or metadata.get("Round Number") or "Round 1").strip()
    query_string = f"interview questions for {role_for_query} {round_for_query}"
    print("\n Querying:", query_string)
    if metadata_filter:
        print("Using metadata filter:", metadata_filter)

    # Encode and query Pinecone
    #qvec = embed_model.encode(query_string).tolist()
    HF_TOKEN = os.getenv("HF_API_KEY", "")

    qvec = _embedder.encode(query_string).tolist()

    res = index.query(
        vector=qvec,
        top_k=10,
        include_metadata=True,
        filter=metadata_filter  # can be None
    )

    matches = res.get("matches", []) or []

    # Optional: keep retry without filter if the strict filter yields nothing
    if not matches and metadata_filter:
        print("No results with filter; retrying without filter…")
        res = index.query(vector=qvec, top_k=10, include_metadata=True)
        matches = res.get("matches", []) or []

    if not matches:
        print(" No results found.")
        return

    results = []

    for m in matches:
        md = m.get("metadata", {}) or {}

        question_text = md.get("text") or ""
        tags = md.get("Tags") or ""

        results.append({
            "question": question_text,
            "tags": tags
        })

    print(results)
    return results


