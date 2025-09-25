# Minimal makefile for BankParser project

.PHONY: help install install-dev test clean docs build

help:
	@echo "BankParser - ePDF Processing Library"
	@echo "================================="
	@echo ""
	@echo "Available commands:"
	@echo "  install     Install the package"
	@echo "  install-dev Install development dependencies"
	@echo "  test        Run tests"
	@echo "  docs        Build documentation"
	@echo "  build       Build package"
	@echo "  clean       Clean build artifacts"
	@echo "  help        Show this help message"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest

docs:
	cd docs && make html

build:
	python -m build

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
