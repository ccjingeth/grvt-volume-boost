from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path

from grvt_volume_boost.secure_files import ensure_private_dir, restrict_file


@unittest.skipIf(os.name == "nt", "POSIX permission semantics are different on Windows")
class SecureFilesTests(unittest.TestCase):
    def test_ensure_private_dir_sets_700(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "private"
            ensure_private_dir(p)
            mode = stat.S_IMODE(p.stat().st_mode)
            self.assertEqual(mode, 0o700)

    def test_restrict_file_sets_600(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "secret.txt"
            p.write_text("secret", encoding="utf-8")
            restrict_file(p)
            mode = stat.S_IMODE(p.stat().st_mode)
            self.assertEqual(mode, 0o600)


if __name__ == "__main__":
    unittest.main()
