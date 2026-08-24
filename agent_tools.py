"""
Agent Tools — Les 2 outils lecture seule de l'agent.
Chaque outil passe par PathGuard avant toute opération I/O.
"""

import os
from path_guard import PathGuard

# Max characters to return from a file read (protects LLM context window)
MAX_CONTENT_LENGTH = 4000


def list_dir(path: str, guard: PathGuard) -> dict:
    """List files and subdirectories at the given path."""
    allowed, reason = guard.validate(path, action="list_dir")
    if not allowed:
        return {"success": False, "error": reason}

    resolved = guard.resolve(path)

    if not os.path.isdir(resolved):
        return {"success": False, "error": f"Ce n'est pas un dossier : {resolved}"}

    entries = []
    try:
        for item in sorted(os.listdir(resolved)):
            full_path = os.path.join(resolved, item)
            if os.path.isdir(full_path):
                entries.append(f"📁 {item}/")
            else:
                size = os.path.getsize(full_path)
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                entries.append(f"📄 {item} ({size_str})")
    except PermissionError:
        return {"success": False, "error": f"Permission refusée : {resolved}"}

    return {
        "success": True,
        "path": resolved,
        "count": len(entries),
        "entries": entries,
    }


def read_file(path: str, guard: PathGuard) -> dict:
    """Read the text content of a file (truncated if too long)."""
    allowed, reason = guard.validate(path, action="read_file")
    if not allowed:
        return {"success": False, "error": reason}

    resolved = guard.resolve(path)

    if not os.path.isfile(resolved):
        return {"success": False, "error": f"Ce n'est pas un fichier : {resolved}"}

    try:
        with open(resolved, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(MAX_CONTENT_LENGTH + 1)

        truncated = len(content) > MAX_CONTENT_LENGTH
        if truncated:
            content = content[:MAX_CONTENT_LENGTH]

        return {
            "success": True,
            "path": resolved,
            "content": content,
            "truncated": truncated,
        }
    except Exception as e:
        return {"success": False, "error": f"Erreur de lecture : {str(e)}"}


# ─── Tool registry (used by agent_core) ────────────────────

TOOLS_DESCRIPTION = """
You have access to exactly 2 tools. Use them to help the user explore files.

TOOL 1: list_dir
  Description: Lists all files and subdirectories at a given path.
  Usage: ACTION: list_dir | <path>
  Example: ACTION: list_dir | .
  Example: ACTION: list_dir | reports/2024

TOOL 2: read_file
  Description: Reads the text content of a single file.
  Usage: ACTION: read_file | <path>
  Example: ACTION: read_file | README.md
  Example: ACTION: read_file | src/config.yaml
"""

TOOL_FUNCTIONS = {
    "list_dir": list_dir,
    "read_file": read_file,
}
