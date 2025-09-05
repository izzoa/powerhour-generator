# Makefile for PowerHour Generator
# Provides convenient commands for building, testing, and packaging

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
PYINSTALLER := $(PYTHON) -m PyInstaller
VERSION := 1.0.0
PROJECT := PowerHourGenerator

# Platform detection
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    PLATFORM := linux
    ARCHIVE_EXT := tar.gz
endif
ifeq ($(UNAME_S),Darwin)
    PLATFORM := macos
    ARCHIVE_EXT := tar.gz
endif
ifeq ($(OS),Windows_NT)
    PLATFORM := windows
    ARCHIVE_EXT := zip
endif

# Directories
DIST_DIR := dist
BUILD_DIR := build
RELEASE_DIR := releases
DOCS_DIR := docs

# Default target
.DEFAULT_GOAL := help

# Phony targets
.PHONY: help clean install install-dev test lint format build build-exe build-wheel build-source release run run-gui run-cli docs check-deps

help:  ## Show this help message
	@echo "PowerHour Generator Build System"
	@echo "================================"
	@echo ""
	@echo "Available targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make install        # Install dependencies"
	@echo "  make test          # Run tests"
	@echo "  make build         # Build executable"
	@echo "  make release       # Create release package"

clean:  ## Clean build artifacts and cache files
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf $(DIST_DIR) $(BUILD_DIR) $(RELEASE_DIR)
	@rm -rf *.egg-info .pytest_cache .coverage htmlcov
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.log" -delete
	@echo "✅ Clean complete"

install:  ## Install runtime dependencies
	@echo "📦 Installing runtime dependencies..."
	@$(PIP) install -r requirements.txt
	@echo "✅ Runtime dependencies installed"

install-dev:  ## Install development dependencies
	@echo "📦 Installing development dependencies..."
	@$(PIP) install -r requirements-dev.txt
	@echo "✅ Development dependencies installed"

test:  ## Run test suite
	@echo "🧪 Running tests..."
	@if [ -d "tests" ]; then \
		$(PYTEST) tests/ -v --cov=. --cov-report=term-missing; \
	else \
		echo "⚠️  No tests directory found. Skipping tests."; \
	fi

lint:  ## Run code linting
	@echo "🔍 Running code linting..."
	@$(PYTHON) -m flake8 powerhour/*.py --max-line-length=120 --ignore=E203,W503 || true
	@$(PYTHON) -m pylint powerhour/*.py --max-line-length=120 || true
	@$(PYTHON) -m mypy powerhour/*.py --ignore-missing-imports || true
	@echo "✅ Linting complete"

format:  ## Format code with black
	@echo "🎨 Formatting code..."
	@$(PYTHON) -m black powerhour/*.py tests/*.py --line-length=120
	@$(PYTHON) -m isort powerhour/*.py tests/*.py
	@echo "✅ Code formatted"

build: build-exe  ## Build executable (default)

build-exe:  ## Build standalone executable
	@echo "🔨 Building executable for $(PLATFORM)..."
	@mkdir -p $(DIST_DIR)
	@$(PYINSTALLER) powerhour.spec --clean --noconfirm
	@echo "✅ Executable built in $(DIST_DIR)/$(PROJECT)"

build-wheel:  ## Build Python wheel
	@echo "🎡 Building wheel distribution..."
	@$(PYTHON) setup.py bdist_wheel
	@echo "✅ Wheel built in $(DIST_DIR)"

build-source:  ## Build source distribution
	@echo "📦 Building source distribution..."
	@$(PYTHON) setup.py sdist
	@echo "✅ Source distribution built in $(DIST_DIR)"

build-all: build-exe build-wheel build-source  ## Build all distribution types

release: build-exe  ## Create release package
	@echo "📦 Creating release package..."
	@mkdir -p $(RELEASE_DIR)
	@$(eval RELEASE_NAME := $(PROJECT)-$(VERSION)-$(PLATFORM))
	@$(eval RELEASE_PATH := $(RELEASE_DIR)/$(RELEASE_NAME))
	@rm -rf $(RELEASE_PATH)
	@mkdir -p $(RELEASE_PATH)
	@cp -r $(DIST_DIR)/$(PROJECT) $(RELEASE_PATH)/
	@mkdir -p $(RELEASE_PATH)/docs
	@cp README.md LICENSE $(RELEASE_PATH)/ 2>/dev/null || true
	@cp -r docs/* $(RELEASE_PATH)/docs/ 2>/dev/null || true
	@if [ "$(PLATFORM)" = "windows" ]; then \
		cd $(RELEASE_DIR) && zip -r $(RELEASE_NAME).zip $(RELEASE_NAME); \
	else \
		cd $(RELEASE_DIR) && tar -czf $(RELEASE_NAME).$(ARCHIVE_EXT) $(RELEASE_NAME); \
	fi
	@rm -rf $(RELEASE_PATH)
	@echo "✅ Release package created: $(RELEASE_DIR)/$(RELEASE_NAME).$(ARCHIVE_EXT)"

run: run-gui  ## Run the application (GUI mode)

run-gui:  ## Run GUI application
	@echo "🚀 Starting PowerHour Generator GUI..."
	@$(PYTHON) -m powerhour.powerhour_gui

run-cli:  ## Run CLI application
	@echo "🚀 Starting PowerHour Generator CLI..."
	@$(PYTHON) -m powerhour.powerhour_generator

docs:  ## Generate documentation
	@echo "📚 Generating documentation..."
	@mkdir -p $(DOCS_DIR)
	@if command -v sphinx-build >/dev/null 2>&1; then \
		sphinx-build -b html . $(DOCS_DIR); \
		echo "✅ Documentation generated in $(DOCS_DIR)"; \
	else \
		echo "⚠️  Sphinx not installed. Install with: pip install sphinx"; \
	fi

check-deps:  ## Check if all dependencies are available
	@echo "🔍 Checking dependencies..."
	@echo -n "  Python: "; $(PYTHON) --version
	@echo -n "  pip: "; $(PIP) --version
	@echo -n "  FFmpeg: "; ffmpeg -version 2>/dev/null | head -n1 || echo "NOT FOUND - Please install FFmpeg"
	@echo -n "  FFprobe: "; ffprobe -version 2>/dev/null | head -n1 || echo "NOT FOUND - Please install FFmpeg"
	@echo -n "  yt-dlp: "; yt-dlp --version 2>/dev/null || echo "NOT FOUND (optional)"
	@echo -n "  PyInstaller: "; $(PYINSTALLER) --version 2>/dev/null || echo "NOT FOUND - Install with: pip install pyinstaller"
	@echo "✅ Dependency check complete"

dev-setup: clean install-dev check-deps  ## Complete development environment setup
	@echo "✅ Development environment ready!"

quick-build: clean install build  ## Quick build (clean, install, build)
	@echo "✅ Quick build complete!"

package-pip:  ## Create pip-installable package
	@echo "📦 Creating pip package..."
	@$(PYTHON) setup.py sdist bdist_wheel
	@echo "✅ Package created. Install with: pip install dist/*.whl"

upload-test:  ## Upload to TestPyPI (requires credentials)
	@echo "📤 Uploading to TestPyPI..."
	@$(PYTHON) -m twine upload --repository testpypi dist/*

upload-pypi:  ## Upload to PyPI (requires credentials)
	@echo "📤 Uploading to PyPI..."
	@$(PYTHON) -m twine upload dist/*

version:  ## Display version information
	@echo "PowerHour Generator v$(VERSION)"
	@echo "Platform: $(PLATFORM)"
	@echo "Python: $(shell $(PYTHON) --version)"

# Development shortcuts
dev: install-dev lint test  ## Run development checks

ci: clean install test lint build  ## CI/CD pipeline simulation

# Docker targets (optional)
docker-build:  ## Build Docker image
	@echo "🐳 Building Docker image..."
	@docker build -t powerhour-generator:$(VERSION) .

docker-run:  ## Run in Docker container
	@echo "🐳 Running in Docker..."
	@docker run -it --rm -v $(PWD)/output:/output powerhour-generator:$(VERSION)