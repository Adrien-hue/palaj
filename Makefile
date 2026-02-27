.PHONY: test test-ci

test:
	pytest

test-ci:
	pytest --cov=core --cov=backend --cov-report=term-missing --cov-fail-under=80
