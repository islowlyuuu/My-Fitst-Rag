"""Git sync helpers."""
import subprocess
from pathlib import Path

from .config import ROOT_DIR


def _git(*args: str, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(ROOT_DIR),
        capture_output=capture,
        text=True,
        encoding="utf-8",
    )


def is_git_repo() -> bool:
    result = _git("rev-parse", "--git-dir")
    return result.returncode == 0


def init() -> str:
    if is_git_repo():
        return "Already a git repository."
    result = _git("init")
    if result.returncode != 0:
        return f"git init failed: {result.stderr}"
    return "Initialized git repository."


def status() -> str:
    if not is_git_repo():
        return "Not a git repository. Run 'kb init' first."
    result = _git("status", "--short")
    return result.stdout or "(clean)"


def sync(message: str = "Update notes") -> str:
    """Add notes, commit, and push."""
    if not is_git_repo():
        return "Not a git repository. Run 'kb init' first."

    _git("add", "notes/")

    status_result = _git("diff", "--cached", "--quiet")
    if status_result.returncode == 0:
        return "Nothing to commit."

    commit_result = _git("commit", "-m", message)
    if commit_result.returncode != 0:
        return f"Commit failed: {commit_result.stderr}"

    push_result = _git("push", "-u", "origin", "HEAD")
    if push_result.returncode != 0:
        stderr = push_result.stderr.strip()
        if "No configured push destination" in stderr or "remote origin" in stderr.lower():
            return "Committed locally. Set a remote with 'git remote add origin <url>' to push."
        return f"Push failed: {stderr}"

    return "Synced successfully."
