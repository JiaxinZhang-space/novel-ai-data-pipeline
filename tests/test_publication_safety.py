from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_public_repo.py"
SPEC = importlib.util.spec_from_file_location("check_public_repo", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
CHECK_PUBLIC_REPO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK_PUBLIC_REPO)


class PublicationSafetyTests(unittest.TestCase):
    def _minimal_root(self, root: Path) -> None:
        (root / "README.md").write_text(
            "SYNTHETIC_PORTFOLIO_DEMO\n",
            encoding="utf-8",
            newline="\n",
        )

    def test_current_repository_passes_publication_gate(self) -> None:
        self.assertEqual(CHECK_PUBLIC_REPO.scan_repository(REPO_ROOT), [])

    def test_detects_private_file_and_local_user_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._minimal_root(root)
            (root / ".env.production").write_text("SAFE=demo\n", encoding="utf-8")
            local_path = "C:" + "\\Users\\Alice\\private.txt"
            (root / "notes.md").write_text(local_path, encoding="utf-8")

            findings = CHECK_PUBLIC_REPO.scan_repository(root)

        self.assertTrue(any("environment file" in item for item in findings))
        self.assertTrue(any("Windows user profile path" in item for item in findings))

    def test_requires_demo_marker_on_artifact_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._minimal_root(root)
            artifact = root / "artifacts" / "datasets" / "unsafe.jsonl"
            artifact.parent.mkdir(parents=True)
            artifact.write_text('{"demo":false}\n', encoding="utf-8", newline="\n")

            findings = CHECK_PUBLIC_REPO.scan_repository(root)

        self.assertTrue(any("demo=true is required" in item for item in findings))


if __name__ == "__main__":
    unittest.main()
