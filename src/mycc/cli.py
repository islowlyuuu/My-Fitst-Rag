"""CLI entry point."""
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .config import NOTES_DIR, TOP_K_DEFAULT
from .indexer import run_index, get_index_stats
from .retriever import search
from .sync import init, status, sync

app = typer.Typer(name="kb", help="AI-first personal knowledge base")
console = Console()


@app.command()
def add(
    path: str = typer.Argument(..., help="Path to a markdown file to add"),
):
    """Add a markdown note to the knowledge base."""
    src = Path(path).resolve()
    if not src.exists():
        console.print(f"[red]File not found: {path}[/red]")
        raise typer.Exit(1)

    dest = NOTES_DIR / src.name
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    console.print(f"[green]Added:[/green] {dest.relative_to(NOTES_DIR)}")


@app.command()
def index(
    force: bool = typer.Option(False, "--force", "-f", help="Full rebuild of the index"),
):
    """Build or update the vector index."""
    console.print("[bold]Indexing...[/bold]")
    num_files, num_chunks = run_index(force=force)

    if num_files == 0 and num_chunks == 0:
        console.print("[yellow]Nothing to index. Add some notes first.[/yellow]")
    else:
        console.print(f"[green]Indexed {num_files} files, {num_chunks} chunks.[/green]")


@app.command()
def query(
    q: str = typer.Argument(..., help="Search query"),
    top_k: int = typer.Option(TOP_K_DEFAULT, "-k", "--top-k", help="Number of results"),
    tag: str | None = typer.Option(None, "--tag", help="Filter by tag"),
):
    """Search the knowledge base."""
    results = search(q, top_k=top_k, tag=tag)

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    table = Table(title=f"Results for: {q}")
    table.add_column("#", style="dim", width=3)
    table.add_column("Score", style="green", width=8)
    table.add_column("Title", style="bold")
    table.add_column("File", style="dim")
    table.add_column("Preview", max_width=60)

    for i, r in enumerate(results, 1):
        preview = r["content"].replace("\n", " ")[:80]
        table.add_row(
            str(i),
            f"{r['score']:.3f}",
            r["title"],
            r["file"],
            preview,
        )

    console.print(table)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind address"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
):
    """Start the RAG API server."""
    import uvicorn
    from .api import create_app

    fastapi_app = create_app()
    console.print(f"[bold green]Starting API server at http://{host}:{port}[/bold green]")
    uvicorn.run(fastapi_app, host=host, port=port)


@app.command(name="init")
def init_cmd():
    """Initialize git repository for the knowledge base."""
    console.print(init())


@app.command(name="sync")
def sync_cmd(
    message: str = typer.Option("Update notes", "-m", "--message", help="Commit message"),
):
    """Sync notes to git remote."""
    console.print(sync(message))


@app.command(name="status")
def status_cmd():
    """Show knowledge base status."""
    stats = get_index_stats()
    console.print(f"[bold]Notes:[/bold] {stats['num_notes']} files")
    console.print(f"[bold]Chunks:[/bold] {stats['num_chunks']}")
    console.print(f"[bold]Last indexed:[/bold] {stats['last_indexed']}")
    console.print()
    console.print("[bold]Git status:[/bold]")
    console.print(status())
