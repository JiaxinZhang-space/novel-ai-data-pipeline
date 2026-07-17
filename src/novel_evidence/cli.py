"""CLI entry point for the V0.1 DEMO evidence pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .pipeline import run_demo_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="novel-evidence",
        description=(
            "Build deterministic synthetic DEMO artifacts. Existing generated "
            "subdirectories inside --output-dir are replaced."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts"),
        help="Artifact root (default: artifacts).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the JSON run summary.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_demo_pipeline(args.output_dir)
    if not args.quiet:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
