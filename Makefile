# All targets run through the project venv (symlink .venv -> ~/.venvs/bluranything).
PY := .venv/bin/python

.PHONY: setup fmt lint type test cov deadcode audit check run build clean

setup: ## Create external venv (iCloud-safe), install dev deps and hooks
	./scripts/setup-venv.sh
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"
	$(PY) -m pre_commit install

fmt: ## Auto-format and fix lint issues
	$(PY) -m ruff format .
	$(PY) -m ruff check --fix .

lint: ## Check formatting and lint
	$(PY) -m ruff format --check .
	$(PY) -m ruff check .

type: ## Static type checking
	$(PY) -m mypy src tests scripts

test: ## Run the test suite
	$(PY) -m pytest

cov: ## Tests with coverage report
	$(PY) -m pytest --cov --cov-report=term-missing

deadcode: ## Scan for dead code
	$(PY) -m vulture

audit: ## Audit dependencies for known vulnerabilities
	$(PY) -m pip_audit

check: lint type test deadcode ## All quality gates

run: ## Launch the app from source
	$(PY) -m bluranything

build: ## Build sdist and wheel into dist/
	$(PY) -m build

clean: ## Remove caches and build artifacts
	rm -rf build dist src/*.egg-info .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
