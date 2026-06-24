.PHONY: setup test lint sample-pass sample-risky api-smoke clean

setup:
	python3 -m venv .venv
	. .venv/bin/activate && python -m pip install --upgrade pip
	. .venv/bin/activate && python -m pip install -e '.[dev]'

test:
	. .venv/bin/activate && pytest

lint:
	. .venv/bin/activate && ruff check .

sample-pass:
	. .venv/bin/activate && rollback-decision samples/safe_release.json

sample-risky:
	. .venv/bin/activate && rollback-decision samples/risky_release.json --output reports/risky_release_report.json || true

api-smoke:
	. .venv/bin/activate && python scripts/api_smoke.py

clean:
	rm -rf .pytest_cache .ruff_cache reports/*.json
