from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .evaluator import evaluate_release
from .models import ReleaseEvidence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate release rollback evidence.")
    parser.add_argument("evidence", type=Path, help="Path to release evidence JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the JSON report.")
    parser.add_argument(
        "--fail-on-rollback",
        action="store_true",
        help="Exit 2 when the recommendation is rollback, useful for release gates.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    evidence = ReleaseEvidence.model_validate_json(args.evidence.read_text(encoding="utf-8"))
    report = evaluate_release(evidence)
    rendered = json.dumps(report.model_dump(), indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)

    if args.fail_on_rollback and report.decision == "rollback":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
