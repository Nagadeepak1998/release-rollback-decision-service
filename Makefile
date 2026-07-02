.PHONY: setup test lint sample-pass sample-risky review-report api-smoke clean

setup:
	python3 -m venv .venv
	. .venv/bin/activate && python -m pip install --upgrade pip
	. .venv/bin/activate && python -m pip install -e '.[dev]'

test:
	. .venv/bin/activate && PYTHONPATH=src pytest

lint:
	. .venv/bin/activate && ruff check .

sample-pass:
	. .venv/bin/activate && PYTHONPATH=src python -m release_rollback.cli samples/safe_release.json

sample-risky:
	. .venv/bin/activate && PYTHONPATH=src python -m release_rollback.cli samples/risky_release.json --output reports/risky_release_report.json || true

review-report:
	. .venv/bin/activate && PYTHONPATH=src python -m release_rollback.cli review samples/post_deploy_review.json --output reports/post_deploy_review.json --markdown reports/post_deploy_review.md --fail-on-rollback || test $$? -eq 2

api-smoke:
	. .venv/bin/activate && PYTHONPATH=src python scripts/api_smoke.py

clean:
	rm -rf .pytest_cache .ruff_cache reports/*.json
