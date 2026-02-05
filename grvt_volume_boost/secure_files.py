from __future__ import annotations

import os
from pathlib import Path


def ensure_private_dir(path: Path) -> None:
    """Create directory (if needed) and restrict to user-only permissions."""
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, 0o700)
    except Exception:
        # Best effort on platforms/filesystems that do not support chmod semantics.
        pass


def restrict_file(path: Path) -> None:
    """Restrict file permissions to user read/write only."""
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass
