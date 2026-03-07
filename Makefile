.PHONY: format lint test check

format:
	black .

lint:
	ruff check .

test:
	pytest

check:
	black --check .
	ruff check .
	pytest
