from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .evaluator import evaluate_release, render_markdown_review, review_post_deploy_evidence
from .models import PostDeployReviewRequest, ReleaseEvidence


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


def build_review_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Review multiple post-deploy evidence windows for one release."
    )
    parser.add_argument("manifest", type=Path, help="Path to post-deploy review JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the JSON review.")
    parser.add_argument("--markdown", type=Path, help="Optional path for the Markdown review.")
    parser.add_argument(
        "--fail-on-rollback",
        action="store_true",
        help="Exit 2 when any reviewed window makes the final decision rollback.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "review":
        return review_main(argv[1:])

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


def review_main(argv: list[str] | None = None) -> int:
    args = build_review_parser().parse_args(argv)
    request = PostDeployReviewRequest.model_validate_json(args.manifest.read_text(encoding="utf-8"))
    report = review_post_deploy_evidence(request)
    rendered = json.dumps(report.model_dump(), indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)

    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown_review(report), encoding="utf-8")

    if args.fail_on_rollback and report.decision == "rollback":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
