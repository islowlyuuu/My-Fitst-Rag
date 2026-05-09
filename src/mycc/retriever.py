"""Retriever: query → embedding → LanceDB search."""
import lancedb

from .config import LANCEDB_PATH, TOP_K_DEFAULT, TABLE_NAME
from .indexer import _get_model


def search(query: str, top_k: int = TOP_K_DEFAULT, tag: str | None = None) -> list[dict]:
    """Semantic search over the knowledge base."""
    model = _get_model()
    db = lancedb.connect(str(LANCEDB_PATH))

    if TABLE_NAME not in db.table_names():
        return []

    table = db.open_table(TABLE_NAME)
    query_vec = model.encode([query], normalize_embeddings=True)[0]

    results = (
        table.search(query_vec.tolist())
        .metric("cosine")
        .limit(50 if tag else top_k)
        .to_list()
    )

    formatted = []
    for r in results:
        tags = r.get("tags", "")
        tags_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        if tag and tag not in tags_list:
            continue

        chunk_content = r.get("content", "")
        score = r.get("_distance", 0)
        score = score if score is not None else 0

        formatted.append({
            "score": round(1.0 - float(score), 4),
            "content": chunk_content,
            "title": r.get("title", ""),
            "file": r.get("file_path", ""),
            "tags": tags_list,
        })

        if not tag and len(formatted) >= top_k:
            break

    return formatted
