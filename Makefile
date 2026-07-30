.DEFAULT_GOAL := help

.PHONY: install install-runtime install-desktop-build metadata schema-check quick validate validate-all ci \
	test test-fast test-unit test-property test-architecture test-smoke test-integration test-corpus test-browser \
	coverage lint lint-fix format format-check typecheck \
	deptry imports dead-code complexity docstrings security-static security-deps \
	security package beta-smoke source-audit source-package source-verify desktop-package desktop-verify \
	mutation mutation-results mutation-browse mutation-clean doctor outdated clean help

PYTHON ?= python
PIP := $(PYTHON) -m pip
SRC_DIRS := src tests
PYTEST_DETERMINISTIC_MARKERS := not browser and not property
PYTEST_FAST_MARKERS := $(PYTEST_DETERMINISTIC_MARKERS) and not corpus
PYTEST_COVERAGE_MARKERS := not browser and not property
PROPERTY_TEST_PATHS := $(shell find tests -type f -name 'test_*_properties.py' -print | sort)
PROPERTY_IGNORE_ARGS := $(addprefix --ignore=,$(PROPERTY_TEST_PATHS))
BROWSER_IGNORE_ARGS := --ignore=tests/browser
SOURCE_SNAPSHOT_PATH ?= dist/source/adventure-graph-0.10.0-source.zip

install:
	$(PIP) install -e ".[dev]"

install-runtime:
	$(PIP) install -e .

install-desktop-build:
	$(PIP) install -r packaging/desktop-build-requirements.txt
	$(PIP) install --no-build-isolation --no-deps -e .
	$(PIP) check

metadata:
	$(PIP) check

schema-check:
	PYTHONPATH=src $(PYTHON) scripts/validate_json_schemas.py

quick: format-check typecheck schema-check test-unit test-smoke

validate: metadata format-check typecheck schema-check test-property coverage deptry imports source-audit

validate-all: validate dead-code complexity docstrings security

ci: validate-all package beta-smoke source-package

test:
	$(PYTHON) -m pytest $(PROPERTY_IGNORE_ARGS) $(BROWSER_IGNORE_ARGS) -m "$(PYTEST_DETERMINISTIC_MARKERS)"

test-fast:
	$(PYTHON) -m pytest $(PROPERTY_IGNORE_ARGS) $(BROWSER_IGNORE_ARGS) -m "$(PYTEST_FAST_MARKERS)"

test-unit:
	$(PYTHON) -m pytest tests/unit $(PROPERTY_IGNORE_ARGS)

test-property:
	$(PYTHON) -c "import hypothesis"
	$(PYTHON) -m pytest $(PROPERTY_TEST_PATHS) -m property

test-architecture:
	$(PYTHON) -m pytest $(PROPERTY_IGNORE_ARGS) $(BROWSER_IGNORE_ARGS) -m architecture

test-smoke:
	$(PYTHON) -m pytest $(PROPERTY_IGNORE_ARGS) $(BROWSER_IGNORE_ARGS) -m smoke

test-integration:
	$(PYTHON) -m pytest tests/integration -m "$(PYTEST_DETERMINISTIC_MARKERS)"

test-corpus:
	$(PYTHON) -m pytest $(PROPERTY_IGNORE_ARGS) $(BROWSER_IGNORE_ARGS) -m corpus

test-browser:
	$(PYTHON) -m pytest tests/browser -m browser

coverage:
	$(PYTHON) -m pytest $(PROPERTY_IGNORE_ARGS) $(BROWSER_IGNORE_ARGS) -m "$(PYTEST_COVERAGE_MARKERS)" --cov=adventure_graph --cov-report=term-missing --cov-report=xml

lint:
	$(PYTHON) -m ruff check $(SRC_DIRS)

lint-fix:
	$(PYTHON) -m ruff check --fix $(SRC_DIRS)

format:
	$(PYTHON) -m ruff format $(SRC_DIRS)
	$(PYTHON) -m ruff check --fix $(SRC_DIRS)

format-check:
	$(PYTHON) -m ruff format --check $(SRC_DIRS)
	$(PYTHON) -m ruff check $(SRC_DIRS)

typecheck:
	$(PYTHON) -m pyright

deptry:
	$(PYTHON) -m deptry .

imports:
	lint-imports

dead-code:
	$(PYTHON) -m vulture src tests --min-confidence 80

complexity:
	$(PYTHON) -m radon cc src --min B
	$(PYTHON) -m radon mi src --min B

docstrings:
	dfc --check src/

security-static:
	$(PYTHON) -m bandit -c pyproject.toml -r src -q

security-deps:
	$(PYTHON) -m pip_audit

security: security-static security-deps

package:
	rm -rf dist
	$(PIP) wheel --no-build-isolation --no-deps --wheel-dir dist .

beta-smoke: package
	$(PYTHON) scripts/beta_smoke.py --wheel-dir dist

source-audit:
	$(PYTHON) scripts/source_snapshot.py audit

source-package:
	$(PYTHON) scripts/source_snapshot.py build $(SOURCE_SNAPSHOT_PATH)

source-verify:
	$(PYTHON) scripts/source_snapshot.py verify $(SOURCE_SNAPSHOT_PATH)

desktop-package:
	$(PYTHON) scripts/build_desktop.py

desktop-verify:
	$(PYTHON) scripts/verify_desktop_artifacts.py $${DESKTOP_ARTIFACT_DIR:-dist/desktop}

mutation:
	$(PYTHON) -m mutmut run

mutation-results:
	$(PYTHON) -m mutmut results

mutation-browse:
	$(PYTHON) -m mutmut browse

mutation-clean:
	rm -rf .mutmut-cache mutants

doctor:
	$(PYTHON) --version
	$(PIP) --version
	$(PYTHON) -m ruff --version
	$(PYTHON) -m pyright --version
	$(PYTHON) -m pytest --version

outdated:
	$(PIP) list --outdated

clean:
	$(PYTHON) scripts/clean_repository.py

help:
	@echo "Setup:"
	@echo "  make install          Install package and developer tools in the active environment"
	@echo "  make install-runtime  Install only the runtime package"
	@echo "  make install-desktop-build Install runtime plus the desktop bundler"
	@echo "  make doctor           Print key tool versions"
	@echo ""
	@echo "Daily loop:"
	@echo "  make quick            Fast confidence loop: format-check, Pyright, unit, smoke"
	@echo "  make format           Format code and apply safe Ruff fixes"
	@echo "  make format-check     Verify formatting and lint rules without modifying files"
	@echo "  make validate         Main local/CI gate, including schemas and branch coverage"
	@echo "  make validate-all     Validate plus dead-code, complexity, docs, and security gates"
	@echo "  make ci               Validate, build a wheel, and run the clean beta smoke"
	@echo ""
	@echo "Tests:"
	@echo "  make test             Run all local deterministic tests, including corpus contracts"
	@echo "  make test-fast        Run local runtime tests without the source development corpus"
	@echo "  make test-unit        Run unit tests"
	@echo "  make test-property    Run property-marked tests wherever they live"
	@echo "  make test-integration Run local integration tests"
	@echo "  make test-corpus      Run source development-corpus and editorial regression contracts"
	@echo "  make test-browser     Run executable Chromium interface tests"
	@echo "  make test-architecture Run static architecture tests"
	@echo "  make test-smoke       Run import and CLI entry-point smoke tests"
	@echo "  make coverage         Run deterministic tests with branch-coverage reporting"
	@echo "  make schema-check     Validate canonical and sparse-compatible JSON against schemas"
	@echo ""
	@echo "Quality tools:"
	@echo "  make lint             Run Ruff lint checks"
	@echo "  make lint-fix         Run Ruff auto-fixes without formatting"
	@echo "  make typecheck        Run strict Pyright over production source"
	@echo "  make deptry           Check dependency declarations"
	@echo "  make imports          Enforce Import Linter architecture contracts"
	@echo "  make dead-code        Run vulture"
	@echo "  make complexity       Run radon complexity and maintainability checks"
	@echo "  make docstrings       Run docstring-format-checker on src/"
	@echo "  make security-static  Run Bandit against src/"
	@echo "  make security-deps    Audit installed dependencies for known vulnerabilities"
	@echo "  make mutation         Run mutation testing"
	@echo ""
	@echo "Packaging and maintenance:"
	@echo "  make package          Build the beta wheel in dist/"
	@echo "  make beta-smoke       Exercise the clean wheel through the installed beta workflow"
	@echo "  make source-audit     Check source-tree paths against the portable snapshot budget"
	@echo "  make source-package   Build and verify a source ZIP with a short stable internal root"
	@echo "  make source-verify    Verify an existing source snapshot at SOURCE_SNAPSHOT_PATH"
	@echo "  make desktop-package  Build, smoke-test, and archive this platform desktop bundle"
	@echo "  make desktop-verify   Verify downloaded desktop archives and adjacent manifests"
	@echo "  make outdated         Show outdated installed packages"
	@echo "  make clean            Remove local generated artifacts"
