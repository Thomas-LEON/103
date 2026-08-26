"""
PathGuard — Validation de chemins fichiers pour l'agent.
Vérifie que chaque accès reste dans le périmètre autorisé.
V2: Supporte les opérations d'écriture (copy_file, write_file) avec backup auto.
"""

import os
import shutil
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

# Protected extensions — cannot be written or overwritten by the agent
PROTECTED_EXTENSIONS = {
    ".py", ".exe", ".dll", ".bat", ".ps1", ".sh",
    ".cmd", ".vbs", ".js", ".msi", ".com", ".scr",
}

# Max file size for reading (500 KB)
MAX_FILE_SIZE = 500 * 1024

# Max content size for write_file (50 000 chars)
MAX_WRITE_SIZE = 50_000


class PathGuard:
    """Validates file paths against security rules before any I/O."""

    def __init__(self, root_dir: str = None):
        raw = os.path.realpath(root_dir or ALLOWED_ROOT_DIR)
        # Ensure trailing separator to prevent prefix collisions
        # e.g. C:\Projects must NOT match C:\ProjectsEvil
        self.root_dir = raw if raw.endswith(os.sep) else raw + os.sep
        self.logs: list[dict] = []

    def resolve(self, path: str) -> str:
        """Resolve a path (relative or absolute) to an absolute real path."""
        if not os.path.isabs(path):
            return os.path.realpath(os.path.join(self.root_dir, path))
        return os.path.realpath(path)

    # ─── Core validation ────────────────────────────────────

    def validate(self, path: str, action: str = "access") -> tuple[bool, str]:
        """
        Validate a path for a given action.
        Returns (allowed: bool, reason: str).
        """
        timestamp = self._timestamp()
        resolved = self.resolve(path)

        # Rule 1: Path traversal detection (check raw input)
        if ".." in path:
            reason = f"Path traversal détecté dans : {path}"
            self._log(timestamp, "❌ BLOCKED", action, path, reason)
            return False, reason

        # Rule 2: Must be under allowed root (resolved path must start with root+sep)
        resolved_check = resolved if resolved.endswith(os.sep) else resolved + os.sep
        if not resolved_check.startswith(self.root_dir) and resolved != self.root_dir.rstrip(os.sep):
            reason = f"Hors périmètre : {resolved} n'est pas sous {self.root_dir}"
            self._log(timestamp, "❌ BLOCKED", action, path, reason)
            return False, reason

        # Rule 3: Path must exist (except for write/create actions)
        if action not in ("write_file", "create_dir", "append_to_file") and not os.path.exists(resolved):
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

        # Rule 9 (write/delete actions): Protected extensions
        if action in ("write_file", "copy_file_dst", "delete_file", "append_to_file"):
            ext = os.path.splitext(resolved)[1].lower()
            if ext in PROTECTED_EXTENSIONS:
                reason = f"Extension protégée : {ext} — opération interdite"
                self._log(timestamp, "❌ BLOCKED", action, path, reason)
                return False, reason

        reason = f"Accès autorisé → {resolved}"
        self._log(timestamp, "✅ ALLOWED", action, path, reason)
        return True, reason

    # ─── Write-specific validation ───────────────────────────

    def validate_write_content(self, content: str) -> tuple[bool, str]:
        """Validate content size for write_file. Rule 8."""
        timestamp = self._timestamp()
        if len(content) > MAX_WRITE_SIZE:
            reason = f"Contenu trop long : {len(content)} chars (max {MAX_WRITE_SIZE})"
            self._log(timestamp, "❌ BLOCKED", "write_file", "(content)", reason)
            return False, reason
        return True, "Taille du contenu OK"

    def validate_copy(self, source: str, destination: str) -> tuple[bool, str]:
        """Validate both source and destination for copy_file. Rule 6."""
        # Validate source (must exist, under root)
        ok_src, reason_src = self.validate(source, action="copy_file_src")
        if not ok_src:
            return False, f"Source invalide — {reason_src}"

        # Validate destination (under root, extension not protected)
        ok_dst, reason_dst = self.validate(destination, action="copy_file_dst")
        if not ok_dst:
            return False, f"Destination invalide — {reason_dst}"

        return True, f"Copie autorisée : {self.resolve(source)} → {self.resolve(destination)}"

    # ─── Backup utility ──────────────────────────────────────

    def backup_if_exists(self, path: str) -> str | None:
        """
        Rule 7: If a file already exists at path, create a .bak copy.
        Returns the backup path if created, None otherwise.
        """
        resolved = self.resolve(path)
        if os.path.isfile(resolved):
            timestamp = self._timestamp()
            bak_path = resolved + ".bak"
            # If .bak already exists, add a counter
            counter = 1
            while os.path.exists(bak_path):
                bak_path = f"{resolved}.bak{counter}"
                counter += 1
            try:
                shutil.copy2(resolved, bak_path)
                self._log(timestamp, "💾 BACKUP", "backup", path,
                          f"Backup créé : {bak_path}")
                return bak_path
            except Exception as e:
                self._log(timestamp, "❌ ERROR", "backup", path,
                          f"Échec du backup : {e}")
                return None
        return None

    # ─── Internals ───────────────────────────────────────────

    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

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
