.PHONY: test lint install clean

install:
	pip install -e ".[dev]"

test:
	pytest --cov=ludolog --cov-report=term-missing -q

lint:
	ruff check src tests

clean:
	rm -rf build dist .pytest_cache htmlcov .coverage *.egg-info
