"""FastAPI REST API for the knowledge base."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import NOTES_DIR, TOP_K_DEFAULT
from .indexer import run_index, get_index_stats, get_markdown_files
from .models import SearchRequest
from .retriever import search


def create_app() -> FastAPI:
    app = FastAPI(
        title="mycc — AI Knowledge Base API",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/stats")
    def stats():
        return get_index_stats()

    @app.post("/search")
    def search_endpoint(req: SearchRequest):
        results = search(req.query, top_k=req.top_k, tag=req.tag)
        return {"results": results, "query": req.query}

    @app.get("/notes")
    def list_notes():
        files = get_markdown_files()
        return {
            "notes": [
                {
                    "path": str(f.relative_to(NOTES_DIR)).replace("\\", "/"),
                    "name": f.stem,
                }
                for f in files
            ]
        }

    @app.get("/notes/{path:path}")
    def get_note(path: str):
        note_path = NOTES_DIR / path
        if not note_path.exists():
            raise HTTPException(status_code=404, detail="Note not found")
        return {
            "path": path,
            "content": note_path.read_text(encoding="utf-8"),
        }

    @app.post("/reindex")
    def reindex(force: bool = True):
        num_files, num_chunks = run_index(force=force)
        return {"indexed_files": num_files, "indexed_chunks": num_chunks}

    return app
