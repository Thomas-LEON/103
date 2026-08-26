"""
Agent Tools — Les 4 outils de l'agent (V2).
V1: list_dir, read_file (lecture seule)
V2: + copy_file, write_file (écriture contrôlée)
Chaque outil passe par PathGuard avant toute opération I/O.
"""

import os
import shutil
import io
from path_guard import PathGuard

try:
    import pandas as pd
    import docx
    HAS_OFFICE_LIBS = True
except ImportError:
    HAS_OFFICE_LIBS = False

# Max characters to return from a file read (protects LLM context window)
MAX_CONTENT_LENGTH = 4000


# ─── TOOL 1: list_dir ───────────────────────────────────────

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


# ─── TOOL 2: read_file ──────────────────────────────────────

def read_file(path: str, guard: PathGuard) -> dict:
    """Read the text content of a file (truncated if too long)."""
    allowed, reason = guard.validate(path, action="read_file")
    if not allowed:
        return {"success": False, "error": reason}

    resolved = guard.resolve(path)

    if not os.path.isfile(resolved):
        return {"success": False, "error": f"Ce n'est pas un fichier : {resolved}"}

    ext = os.path.splitext(resolved)[1].lower()

    try:
        if ext == ".docx":
            if not HAS_OFFICE_LIBS:
                return {"success": False, "error": "Librairies manquantes. Lancez: pip install pandas openpyxl python-docx"}
            doc = docx.Document(resolved)
            content = "\n".join([p.text for p in doc.paragraphs])
        elif ext == ".xlsx":
            if not HAS_OFFICE_LIBS:
                return {"success": False, "error": "Librairies manquantes. Lancez: pip install pandas openpyxl python-docx"}
            df = pd.read_excel(resolved)
            content = df.to_csv(index=False)
        else:
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


# ─── TOOL 3: copy_file ──────────────────────────────────────

def copy_file(args: str, guard: PathGuard) -> dict:
    """
    Copy a file from source to destination.
    Args format: "source | destination"
    """
    parts = args.split("|", 1)
    if len(parts) < 2:
        return {"success": False, "error": "Format requis : copy_file | source | destination"}

    source = parts[0].strip()
    destination = parts[1].strip()

    # Validate both paths via PathGuard
    allowed, reason = guard.validate_copy(source, destination)
    if not allowed:
        return {"success": False, "error": reason}

    resolved_src = guard.resolve(source)
    resolved_dst = guard.resolve(destination)

    if not os.path.isfile(resolved_src):
        return {"success": False, "error": f"La source n'est pas un fichier : {resolved_src}"}

    # Backup destination if it already exists (Rule 7)
    backup_path = guard.backup_if_exists(destination)

    try:
        # Create parent directories if needed
        os.makedirs(os.path.dirname(resolved_dst), exist_ok=True)
        shutil.copy2(resolved_src, resolved_dst)

        result = {
            "success": True,
            "source": resolved_src,
            "destination": resolved_dst,
            "message": f"Fichier copié avec succès.",
        }
        if backup_path:
            result["backup"] = backup_path
            result["message"] += f" Backup de l'ancien fichier : {backup_path}"
        return result

    except Exception as e:
        return {"success": False, "error": f"Erreur de copie : {str(e)}"}


# ─── TOOL 4: write_file ─────────────────────────────────────

def write_file(args: str, guard: PathGuard) -> dict:
    """
    Write content to a file (create or overwrite).
    Args format: "path | content"
    """
    parts = args.split("|", 1)
    if len(parts) < 2:
        return {"success": False, "error": "Format requis : write_file | chemin | contenu"}

    path = parts[0].strip()
    content = parts[1].strip()

    # Validate path via PathGuard
    allowed, reason = guard.validate(path, action="write_file")
    if not allowed:
        return {"success": False, "error": reason}

    # Validate content size (Rule 8)
    ok, size_reason = guard.validate_write_content(content)
    if not ok:
        return {"success": False, "error": size_reason}

    resolved = guard.resolve(path)
    ext = os.path.splitext(resolved)[1].lower()

    # Backup if file already exists (Rule 7)
    backup_path = guard.backup_if_exists(path)

    try:
        # Create parent directories if needed
        os.makedirs(os.path.dirname(resolved), exist_ok=True)
        
        if ext == ".docx":
            if not HAS_OFFICE_LIBS:
                return {"success": False, "error": "Librairies manquantes. Lancez: pip install pandas openpyxl python-docx"}
            doc = docx.Document()
            doc.add_paragraph(content)
            doc.save(resolved)
        elif ext == ".xlsx":
            if not HAS_OFFICE_LIBS:
                return {"success": False, "error": "Librairies manquantes. Lancez: pip install pandas openpyxl python-docx"}
            df = pd.read_csv(io.StringIO(content))
            df.to_excel(resolved, index=False)
        else:
            with open(resolved, "w", encoding="utf-8") as f:
                f.write(content)

        result = {
            "success": True,
            "path": resolved,
            "chars_written": len(content),
            "message": f"Fichier écrit avec succès ({len(content)} caractères).",
        }
        if backup_path:
            result["backup"] = backup_path
            result["message"] += f" Backup de l'ancien fichier : {backup_path}"
        return result

    except Exception as e:
        return {"success": False, "error": f"Erreur d'écriture : {str(e)}"}


# ─── TOOL 5: move_file ──────────────────────────────────────

def move_file(args: str, guard: PathGuard) -> dict:
    """
    Move (or rename) a file from source to destination.
    Args format: "source | destination"
    """
    parts = args.split("|", 1)
    if len(parts) < 2:
        return {"success": False, "error": "Format requis : move_file | source | destination"}

    source = parts[0].strip()
    destination = parts[1].strip()

    # Validate both paths via PathGuard
    allowed, reason = guard.validate_copy(source, destination)
    if not allowed:
        return {"success": False, "error": reason}

    resolved_src = guard.resolve(source)
    resolved_dst = guard.resolve(destination)

    if not os.path.isfile(resolved_src):
        return {"success": False, "error": f"La source n'est pas un fichier : {resolved_src}"}

    # Backup destination if it already exists (Rule 7)
    backup_path = guard.backup_if_exists(destination)

    try:
        # Create parent directories if needed
        os.makedirs(os.path.dirname(resolved_dst), exist_ok=True)
        shutil.move(resolved_src, resolved_dst)

        result = {
            "success": True,
            "source": resolved_src,
            "destination": resolved_dst,
            "message": f"Fichier déplacé avec succès.",
        }
        if backup_path:
            result["backup"] = backup_path
            result["message"] += f" Backup de l'ancien fichier : {backup_path}"
        return result

    except Exception as e:
        return {"success": False, "error": f"Erreur de déplacement : {str(e)}"}


# ─── Tool registry (used by agent_core) ────────────────────

TOOLS_DESCRIPTION = """
You have access to exactly 5 tools. Use them to help the user explore and manage files.

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
  Note: You can natively read .txt, .md, .csv, .docx, and .xlsx files.

TOOL 3: copy_file
  Description: Copies a file from a source path to a destination path.
  Usage: ACTION: copy_file | <source> | <destination>
  Example: ACTION: copy_file | report.md | backup/report_copy.md
  Note: If the destination already exists, a .bak backup is created automatically.
  Note: You CANNOT overwrite protected files (.py, .bat, .ps1, .sh, .exe, .dll).

TOOL 4: write_file
  Description: Creates a new file or overwrites an existing file with the given content.
  Usage: ACTION: write_file | <path> | <content>
  Example: ACTION: write_file | notes/summary.txt | This is the summary of the meeting.
  Note: If the file already exists, a .bak backup is created automatically.
  Note: You CANNOT write to protected extensions (.py, .bat, .ps1, .sh, .exe, .dll).
  Note: Maximum content length is 50,000 characters.
  Note: You can natively write to .docx and .xlsx files.
  CRITICAL: When writing an .xlsx file, your <content> MUST be formatted as raw CSV data (with commas). The system will automatically convert it to a valid Excel workbook. Do NOT tell the user about this CSV conversion, act as if you handle Excel files natively.

TOOL 5: move_file
  Description: Moves or renames a file from a source path to a destination path. The source file is removed after the move.
  Usage: ACTION: move_file | <source> | <destination>
  Example: ACTION: move_file | draft.md | final/report.md
  Example: ACTION: move_file | old_name.txt | new_name.txt
  Note: If the destination already exists, a .bak backup is created automatically.
  Note: You CANNOT overwrite protected files (.py, .bat, .ps1, .sh, .exe, .dll).
  Note: This also works for renaming files in place.
"""

TOOL_FUNCTIONS = {
    "list_dir": list_dir,
    "read_file": read_file,
    "copy_file": copy_file,
    "write_file": write_file,
    "move_file": move_file,
}
