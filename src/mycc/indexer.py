"""Indexer: markdown → chunks → embeddings → LanceDB."""
import json
from datetime import datetime
from pathlib import Path

import frontmatter
import lancedb
from sentence_transformers import SentenceTransformer

from .config import (
    NOTES_DIR,
    LANCEDB_PATH,
    INDEX_META_PATH,
    EMBEDDING_MODEL,
    EMBEDDING_DEVICE,
    TABLE_NAME,
)
from .models import Chunk, IndexMeta

_embedding_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)
    return _embedding_model


def _read_note(file_path: Path) -> frontmatter.Post | None:
    try:
        post = frontmatter.load(str(file_path))
        return post
    except Exception:
        return None


def _split_by_headings(markdown_content: str) -> list[str]:
    """Split markdown content by ## headings into chunks."""
    lines = markdown_content.split("\n")
    chunks = []
    current = []

    for line in lines:
        if line.startswith("## "):
            if current:
                chunks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        chunks.append("\n".join(current).strip())

    return chunks if chunks else [markdown_content]


def _parse_note(file_path: Path) -> list[Chunk]:
    """Parse a markdown file into chunks."""
    post = _read_note(file_path)
    if post is None:
        return []

    relative_path = str(file_path.relative_to(NOTES_DIR)).replace("\\", "/")
    title = post.get("title", file_path.stem)
    tags = post.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    created = str(post.get("created", ""))

    content = post.content or ""
    sections = _split_by_headings(content)

    chunks = []
    for i, section in enumerate(sections):
        chunk = Chunk(
            title=title,
            file_path=relative_path,
            chunk_index=i,
            content=section,
            tags=tags,
            created=created,
        )
        chunks.append(chunk)
    return chunks


def _load_index_meta() -> IndexMeta:
    if INDEX_META_PATH.exists():
        try:
            data = json.loads(INDEX_META_PATH.read_text(encoding="utf-8"))
            return IndexMeta(**data)
        except Exception:
            pass
    return IndexMeta()


def _save_index_meta(meta: IndexMeta):
    INDEX_META_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_META_PATH.write_text(meta.model_dump_json(), encoding="utf-8")


def get_markdown_files() -> list[Path]:
    """Return all markdown files in the notes directory."""
    if not NOTES_DIR.exists():
        return []
    return sorted(NOTES_DIR.rglob("*.md"))


def _to_row(chunk: Chunk, vector: list[float]) -> dict:
    return {
        "id": chunk.id,
        "title": chunk.title,
        "file_path": chunk.file_path,
        "chunk_index": chunk.chunk_index,
        "content": chunk.content,
        "tags": ",".join(chunk.tags),
        "created": chunk.created,
        "vector": vector,
    }


def run_index(force: bool = False) -> tuple[int, int]:
    """Build or update the vector index. Returns (num_files, num_chunks)."""
    model = _get_model()
    meta = _load_index_meta()
    files = get_markdown_files()

    if not files:
        return 0, 0

    current_mtimes: dict[str, float] = {}
    new_chunks: list[Chunk] = []
    processed_files = 0

    for fpath in files:
        rel = str(fpath.relative_to(NOTES_DIR)).replace("\\", "/")
        mtime = fpath.stat().st_mtime
        current_mtimes[rel] = mtime

        if not force and rel in meta.file_mtimes and meta.file_mtimes[rel] >= mtime:
            continue

        chunks = _parse_note(fpath)
        if chunks:
            new_chunks.extend(chunks)
            processed_files += 1

    if not new_chunks:
        return 0, 0

    texts = [c.content for c in new_chunks]
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    rows = [_to_row(c, emb.tolist()) for c, emb in zip(new_chunks, embeddings)]

    db = lancedb.connect(str(LANCEDB_PATH))

    if TABLE_NAME in db.table_names():
        if force:
            db.drop_table(TABLE_NAME)
            table = db.create_table(TABLE_NAME, data=rows)
        else:
            table = db.open_table(TABLE_NAME)
            indexed_paths = {c.file_path for c in new_chunks}
            for path in indexed_paths:
                try:
                    table.delete(f"file_path = '{path}'")
                except Exception:
                    pass
            table.add(rows)
    else:
        table = db.create_table(TABLE_NAME, data=rows)

    try:
        table.create_fts_index("content", replace=True)
    except Exception:
        pass

    meta.last_indexed = datetime.now().isoformat()
    meta.file_mtimes = current_mtimes
    _save_index_meta(meta)

    return processed_files, len(new_chunks)


def get_index_stats() -> dict:
    """Return current index statistics."""
    files = get_markdown_files()
    meta = _load_index_meta()

    db = lancedb.connect(str(LANCEDB_PATH))
    num_chunks = 0
    if TABLE_NAME in db.table_names():
        num_chunks = db.open_table(TABLE_NAME).count_rows()

    return {
        "num_notes": len(files),
        "num_chunks": num_chunks,
        "last_indexed": meta.last_indexed or "never",
    }
