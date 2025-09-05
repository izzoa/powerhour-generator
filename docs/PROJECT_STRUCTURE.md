# PowerHour Generator - Project Structure

## Overview
This document describes the reorganized project structure following Python best practices.

## Directory Structure

```
powerhour-generator/
│
├── powerhour/                    # Source code package
│   ├── __init__.py              # Package initialization
│   ├── powerhour_gui.py         # GUI application
│   ├── powerhour_processor.py   # Video processing engine
│   └── powerhour_generator.py   # CLI application
│
├── tests/                        # Test suite
│   ├── __init__.py              # Test package initialization
│   └── test_gui.py              # GUI unit tests
│
├── docs/                         # Documentation
│   ├── README_GUI.md            # GUI quick start guide
│   ├── USER_GUIDE.md            # Comprehensive user manual
│   ├── CHANGELOG.md             # Version history
│   ├── CONTRIBUTING.md          # Contribution guidelines
│   ├── ARCHITECTURE.md          # System architecture
│   ├── RELEASE.md               # Release procedures
│   ├── UI_MIGRATION.md          # Migration tracker
│   ├── PROJECT_STRUCTURE.md     # This file
│   └── PHASE*_COMPLETE.md       # Phase completion records
│
├── scripts/                      # Utility scripts
│   ├── build.py                 # Build automation script
│   ├── install_requirements_mac.sh    # macOS installer
│   ├── Install_Requirements_Win.ps1   # Windows installer
│   └── install_requirements_deb.sh    # Linux/Debian installer
│
├── assets/                       # Static assets
│   └── logo.png                 # Application logo
│
├── .github/                      # GitHub configuration
│   └── workflows/               # CI/CD workflows
│       ├── ci.yml               # Continuous integration
│       ├── release.yml          # Release automation
│       └── README.md            # Workflow documentation
│
├── releases/                     # Release artifacts (gitignored)
├── test_videos/                  # Test video files (gitignored)
├── test_output/                  # Test output directory (gitignored)
│
├── README.md                     # Main project README
├── LICENSE                       # MIT License
├── setup.py                      # Python package configuration
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Development dependencies
├── environment.yml               # Conda environment
├── Makefile                      # Build automation commands
├── MANIFEST.in                   # Package manifest
├── powerhour.spec               # PyInstaller configuration
└── .gitignore                   # Git ignore rules
```

## Benefits of This Structure

### 1. **Clear Separation of Concerns**
- Source code is isolated in the `powerhour` package
- Tests are separate from source code
- Documentation has its own dedicated directory
- Scripts and tools are organized separately

### 2. **Python Best Practices**
- Proper package structure with `__init__.py` files
- Tests follow standard `tests/` directory convention
- Source code is importable as a package: `from powerhour import PowerHourGUI`

### 3. **Documentation Organization**
- All markdown documentation in `docs/` folder
- Easy to find and maintain documentation
- GitHub will recognize and display documentation properly

### 4. **Build and Distribution**
- Clean separation of build scripts in `scripts/`
- Static assets in dedicated `assets/` folder
- Proper `setup.py` configuration for pip installation

### 5. **Development Workflow**
- Clear project root with only essential files
- Build artifacts in separate directories (gitignored)
- Test files and outputs in dedicated directories

## Usage Examples

### Running the Application

```bash
# GUI mode (from project root)
python -m powerhour.powerhour_gui

# CLI mode
python -m powerhour.powerhour_generator [args]

# After installation via pip
powerhour-gui
powerhour [args]
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_gui.py

# With coverage
python -m pytest tests/ --cov=powerhour
```

### Building the Project

```bash
# Using Makefile
make build        # Build executable
make test         # Run tests
make clean        # Clean build artifacts
make release      # Create release package

# Using PyInstaller directly
pyinstaller powerhour.spec

# Using setup.py
python setup.py sdist bdist_wheel
```

## Import Examples

```python
# Import from the package
from powerhour import PowerHourGUI, ProcessorThread
from powerhour.powerhour_gui import PowerHourGUI
from powerhour.powerhour_processor import ProcessorThread

# After pip installation
import powerhour
```

## CI/CD Integration

The GitHub Actions workflows have been updated to work with the new structure:

- **ci.yml**: Runs tests from `tests/`, lints code in `powerhour/`
- **release.yml**: Builds from `powerhour/`, includes docs from `docs/`

## Migration Notes

If you have existing code that imports from the old structure:

```python
# Old import
from powerhour_gui import PowerHourGUI

# New import
from powerhour.powerhour_gui import PowerHourGUI
# or
from powerhour import PowerHourGUI
```

## Maintenance

When adding new files:
- Python modules go in `powerhour/`
- Test files go in `tests/` with `test_` prefix
- Documentation goes in `docs/` as Markdown
- Build/install scripts go in `scripts/`
- Images/icons go in `assets/`

This structure ensures the project remains organized and maintainable as it grows.