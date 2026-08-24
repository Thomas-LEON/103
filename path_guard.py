"""
PathGuard — Validation de chemins fichiers pour l'agent.
Vérifie que chaque accès reste dans le périmètre autorisé.
"""

import os
from datetime import datetime

# ============================================================
# ⚠️  CONFIGURATION — Change this to your allowed root directory
# ============================================================
ALLOWED_ROOT_DIR = r"C:\CHANGE_ME"

# Blocked binary extensions (useless for LLM reading)
BLOCKED_EXTENSIONS = {
    ".exe", ".dll", ".bin", ".dat", ".msi", ".iso",
    ".img", ".sys", ".drv", ".ocx", ".com", ".scr",
    ".pdb", ".obj", ".o", ".so", ".dylib",
}

# Max file size in bytes (500 KB)
MAX_FILE_SIZE = 500 * 1024


class PathGuard:
    """Validates file paths against security rules before any I/O."""

    def __init__(self, root_dir: str = None):
        self.root_dir = os.path.realpath(root_dir or ALLOWED_ROOT_DIR)
        self.logs: list[dict] = []

    def resolve(self, path: str) -> str:
        """Resolve a path (relative or absolute) to an absolute real path."""
        if not os.path.isabs(path):
            return os.path.realpath(os.path.join(self.root_dir, path))
        return os.path.realpath(path)

    def validate(self, path: str, action: str = "access") -> tuple[bool, str]:
        """
        Validate a path for a given action.
        Returns (allowed: bool, reason: str).
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        resolved = self.resolve(path)

        # Rule 1: Path traversal detection (check raw input)
        if ".." in path:
            reason = f"Path traversal détecté dans : {path}"
            self._log(timestamp, "❌ BLOCKED", action, path, reason)
            return False, reason

        # Rule 2: Must be under allowed root
        if not resolved.startswith(self.root_dir):
            reason = f"Hors périmètre : {resolved} n'est pas sous {self.root_dir}"
            self._log(timestamp, "❌ BLOCKED", action, path, reason)
            return False, reason

        # Rule 3: Path must exist
        if not os.path.exists(resolved):
            reason = f"Chemin introuvable : {resolved}"
            self._log(timestamp, "❌ NOT FOUND", action, path, reason)
            return False, reason

        # Rule 4 (read_file only): Block binary extensions
        if action == "read_file":
            ext = os.path.splitext(resolved)[1].lower()
            if ext in BLOCKED_EXTENSIONS:
                reason = f"Extension binaire bloquée : {ext}"
                self._log(timestamp, "❌ BLOCKED", action, path, reason)
                return False, reason

            # Rule 5 (read_file only): File size limit
            if os.path.isfile(resolved):
                size = os.path.getsize(resolved)
                if size > MAX_FILE_SIZE:
                    size_kb = size / 1024
                    max_kb = MAX_FILE_SIZE / 1024
                    reason = f"Fichier trop volumineux : {size_kb:.0f} KB (max {max_kb:.0f} KB)"
                    self._log(timestamp, "❌ BLOCKED", action, path, reason)
                    return False, reason

        reason = f"Accès autorisé → {resolved}"
        self._log(timestamp, "✅ ALLOWED", action, path, reason)
        return True, reason

    def _log(self, timestamp: str, verdict: str, action: str, path: str, reason: str):
        self.logs.append({
            "time": timestamp,
            "verdict": verdict,
            "action": action,
            "path": path,
            "reason": reason,
        })

    def get_logs(self) -> list[dict]:
        return list(self.logs)

    def clear_logs(self):
        self.logs.clear()
