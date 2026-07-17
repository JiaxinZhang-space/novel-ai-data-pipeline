"""Fail closed when a public portfolio checkout contains obvious sensitive data.

This is a lightweight release guard, not a substitute for legal, privacy, or
security review. It intentionally uses only the Python standard library so it
can run before optional dependencies are installed.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable, Sequence


DEMO_MARKER = "SYNTHETIC_PORTFOLIO_DEMO"
EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "venv",
}
FORBIDDEN_DIRS = {
    "data/private",
    "evidence/private",
    "secrets",
}
FORBIDDEN_SUFFIXES = {
    ".7z",
    ".db",
    ".key",
    ".p12",
    ".pem",
    ".pfx",
    ".rar",
    ".sqlite",
    ".zip",
}
MAX_PUBLIC_FILE_BYTES = 2 * 1024 * 1024
SELF_PATH = "scripts/check_public_repo.py"

CONTENT_PATTERNS = (
    (
        "private key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("OpenAI-style secret", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    (
        "Windows user profile path",
        re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s\"']+"),
    ),
    (
        "email address",
        re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    ),
    ("mainland China mobile number", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    (
        "mainland China identity number",
        re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)"),
    ),
    (
        "secret-like URL query",
        re.compile(
            r"(?i)https?://[^\s\"']+[?&](?:token|signature|secret|key)="
            r"[^&\s\"']+"
        ),
    ),
)


def _relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _iter_public_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in EXCLUDED_DIRS for part in relative_parts):
            continue
        yield path


def _read_text(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


def _check_artifact_markers(root: Path) -> list[str]:
    findings: list[str] = []
    artifact_root = root / "artifacts"
    if not artifact_root.exists():
        return findings

    for path in sorted(artifact_root.rglob("*.json")):
        relative = _relative_posix(path, root)
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(f"{relative}: invalid JSON ({exc})")
            continue
        if not isinstance(payload, dict) or payload.get("demo") is not True:
            findings.append(f"{relative}: top-level demo=true is required")

    for path in sorted(artifact_root.rglob("*.jsonl")):
        relative = _relative_posix(path, root)
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8-sig").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                findings.append(f"{relative}:{line_number}: invalid JSON ({exc})")
                continue
            if not isinstance(row, dict) or row.get("demo") is not True:
                findings.append(f"{relative}:{line_number}: demo=true is required")
    return findings


def scan_repository(root: Path) -> list[str]:
    root = root.resolve()
    findings: list[str] = []

    readme = root / "README.md"
    if not readme.exists() or DEMO_MARKER not in readme.read_text(encoding="utf-8"):
        findings.append(f"README.md: required marker {DEMO_MARKER!r} is missing")

    for forbidden in sorted(FORBIDDEN_DIRS):
        if (root / Path(forbidden)).exists():
            findings.append(f"{forbidden}: private directory must not be public")

    for path in _iter_public_files(root):
        relative = _relative_posix(path, root)
        lower_name = path.name.lower()
        if lower_name == ".env" or lower_name.startswith(".env."):
            findings.append(f"{relative}: environment file must not be public")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            findings.append(f"{relative}: forbidden sensitive/archive file type")
        if path.stat().st_size > MAX_PUBLIC_FILE_BYTES:
            findings.append(
                f"{relative}: file exceeds {MAX_PUBLIC_FILE_BYTES} byte public limit"
            )

        if relative == SELF_PATH:
            continue
        text = _read_text(path)
        if text is None:
            continue
        for label, pattern in CONTENT_PATTERNS:
            match = pattern.search(text)
            if match:
                line_number = text.count("\n", 0, match.start()) + 1
                findings.append(f"{relative}:{line_number}: possible {label}")

    findings.extend(_check_artifact_markers(root))
    return sorted(set(findings))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (default: inferred from this script).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    findings = scan_repository(args.root)
    if findings:
        print("PUBLIC REPOSITORY SAFETY CHECK: FAILED")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("PUBLIC REPOSITORY SAFETY CHECK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
