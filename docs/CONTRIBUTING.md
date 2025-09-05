# Contributing to PowerHour Video Generator

Thank you for your interest in contributing to PowerHour Video Generator! This document provides guidelines and instructions for contributing to the project.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Code Style Guide](#code-style-guide)
4. [Testing](#testing)
5. [Making Changes](#making-changes)
6. [Pull Request Process](#pull-request-process)
7. [Project Structure](#project-structure)
8. [Development Guidelines](#development-guidelines)
9. [Documentation](#documentation)
10. [Community](#community)

---

## Getting Started

### Prerequisites
Before contributing, ensure you have:
- Python 3.8 or higher
- Git
- FFmpeg installed and in PATH
- A GitHub account
- Basic knowledge of Python and Tkinter

### Types of Contributions

We welcome various types of contributions:
- 🐛 **Bug Fixes**: Fix issues and improve stability
- ✨ **Features**: Add new functionality
- 📚 **Documentation**: Improve guides and docstrings
- 🧪 **Tests**: Add test coverage
- 🎨 **UI/UX**: Enhance the interface
- ⚡ **Performance**: Optimize processing speed
- 🌐 **Translations**: Add language support

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/izzoa/powerhour-generator.git
cd powerhour-generator
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install required packages
pip install -r requirements-dev.txt

# If requirements-dev.txt doesn't exist:
pip install psutil pytest pytest-cov black flake8 mypy
```

### 4. Verify Setup

```bash
# Run the application
python powerhour_gui.py

# Run tests
python -m pytest test_gui.py

# Check code style
flake8 powerhour_gui.py powerhour_processor.py
```

### 5. Configure Git

```bash
# Set up git hooks (optional but recommended)
git config core.hooksPath .githooks

# Configure user
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

---

## Code Style Guide

### Python Style

We follow PEP 8 with these specifications:

```python
# Module docstring
"""
Module description.

Detailed explanation if needed.
"""

# Imports grouped and ordered
import os
import sys
from typing import Optional, List, Dict

import third_party_lib

from local_module import function


# Class definition with comprehensive docstring
class ExampleClass:
    """
    Brief description of the class.
    
    Longer description explaining purpose and usage.
    
    Attributes:
        attribute1 (type): Description
        attribute2 (type): Description
    """
    
    def __init__(self, param: str) -> None:
        """
        Initialize the class.
        
        Args:
            param: Parameter description
            
        Returns:
            None
        """
        self.param = param
    
    def method(self, arg: int) -> bool:
        """
        Method description.
        
        Args:
            arg: Argument description
            
        Returns:
            bool: Return value description
            
        Raises:
            ValueError: When arg is invalid
        """
        if arg < 0:
            raise ValueError("arg must be non-negative")
        return True


# Constants in UPPER_CASE
MAX_VIDEOS = 60
DEFAULT_FADE_DURATION = 3.0

# Functions with type hints
def process_video(path: str, duration: float) -> Optional[str]:
    """Process a video file."""
    pass
```

### Naming Conventions

- **Variables**: `snake_case`
- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`
- **Protected attributes**: `_leading_underscore`

### Code Formatting

Use `black` for automatic formatting:

```bash
# Format single file
black powerhour_gui.py

# Format all Python files
black *.py

# Check without modifying
black --check *.py
```

### Linting

Use `flake8` for style checking:

```bash
# Check all files
flake8 *.py

# With specific rules
flake8 --max-line-length=100 --ignore=E501,W503 *.py
```

### Type Checking

Use `mypy` for type validation:

```bash
# Type check
mypy powerhour_gui.py powerhour_processor.py
```

---

## Testing

### Test Structure

```python
# test_gui.py
import unittest
from unittest.mock import Mock, patch
import tkinter as tk

class TestPowerHourGUI(unittest.TestCase):
    """Test cases for PowerHourGUI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.app = PowerHourGUI()
    
    def tearDown(self):
        """Clean up after tests."""
        self.app.destroy()
    
    def test_input_validation(self):
        """Test input validation methods."""
        # Test video source validation
        self.app.video_source_var.set("/valid/path")
        self.assertTrue(self.app.validate_video_source())
        
    def test_configuration_save(self):
        """Test configuration persistence."""
        with patch('json.dump') as mock_dump:
            self.app.save_config()
            mock_dump.assert_called_once()
```

### Running Tests

```bash
# Run all tests
python -m pytest

# With coverage
python -m pytest --cov=powerhour_gui --cov=powerhour_processor

# Verbose output
python -m pytest -v

# Specific test
python -m pytest test_gui.py::TestPowerHourGUI::test_input_validation
```

### Writing New Tests

1. Create test file: `test_[module].py`
2. Use descriptive test names: `test_[feature]_[condition]_[expected]`
3. Include docstrings explaining what's tested
4. Mock external dependencies
5. Test both success and failure cases

---

## Making Changes

### 1. Create Feature Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Your Changes

Follow this checklist:
- [ ] Write clean, readable code
- [ ] Add docstrings to all functions/classes
- [ ] Include type hints
- [ ] Update relevant documentation
- [ ] Add tests for new functionality
- [ ] Ensure all tests pass
- [ ] Run linters and formatters

### 3. Commit Guidelines

Use clear, descriptive commit messages:

```bash
# Good commit messages
git commit -m "Add progress bar speed indicator"
git commit -m "Fix memory leak in video processing"
git commit -m "Update documentation for preset system"

# Format for longer messages
git commit -m "Add expert mode for advanced users

- Add FFmpeg parameter editing
- Include preset management
- Update UI to show/hide expert panel
- Add tests for new functionality"
```

Commit message prefixes:
- `Add:` New feature or file
- `Fix:` Bug fix
- `Update:` Modification to existing feature
- `Remove:` Deletion of code or files
- `Refactor:` Code restructuring
- `Docs:` Documentation changes
- `Test:` Test additions or changes
- `Style:` Formatting, no code change

### 4. Keep Branch Updated

```bash
# Periodically sync with upstream
git fetch upstream
git rebase upstream/main
```

---

## Pull Request Process

### 1. Before Submitting

Checklist:
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] Branch is up-to-date with main

### 2. Create Pull Request

1. Push your branch:
```bash
git push origin feature/your-feature-name
```

2. Go to GitHub and create PR
3. Use PR template (if available)
4. Fill in description:
   - What changes were made
   - Why they were needed
   - How they were tested
   - Related issues

### 3. PR Title Format

```
[Type] Brief description

Examples:
[Feature] Add keyboard shortcuts for common actions
[Fix] Resolve crash when processing empty folders
[Docs] Improve installation instructions
```

### 4. Code Review

- Respond to feedback promptly
- Make requested changes
- Push updates to same branch
- Mark conversations as resolved

### 5. After Merge

```bash
# Clean up local branch
git checkout main
git pull upstream main
git branch -d feature/your-feature-name
```

---

## Project Structure

```
powerhour-generator/
├── powerhour_gui.py           # Main GUI application
│   ├── PowerHourGUI class     # Main window and UI
│   ├── Validation methods     # Input validation
│   ├── Configuration mgmt     # Settings persistence
│   └── UI builder methods     # Interface construction
│
├── powerhour_processor.py     # Video processing
│   ├── ProcessorThread class  # Threaded processing
│   ├── Video analysis         # Duration, loudness
│   ├── FFmpeg integration     # Encoding, effects
│   └── Queue messaging        # Thread communication
│
├── test_gui.py                # GUI tests
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
│
├── docs/                      # Documentation
│   ├── README_GUI.md         # Quick start
│   ├── USER_GUIDE.md         # User manual
│   ├── ARCHITECTURE.md       # System design
│   └── CHANGELOG.md          # Version history
│
└── config/                    # Configuration
    └── config.json           # User settings
```

---

## Development Guidelines

### GUI Development

#### Adding New UI Elements

1. Add to appropriate build method
2. Configure grid/pack properly
3. Add validation if needed
4. Update configuration persistence
5. Add tooltips for context

Example:
```python
def build_new_section(self):
    """Create new UI section."""
    frame = ttk.LabelFrame(self, text="New Section")
    frame.grid(row=X, column=0, sticky="ew", padx=10, pady=5)
    
    # Add widgets
    self.new_var = tk.StringVar()
    entry = ttk.Entry(frame, textvariable=self.new_var)
    entry.grid(row=0, column=0)
    
    # Add validation
    entry.bind("<FocusOut>", self.validate_new_input)
```

#### Threading Considerations

- Never update UI from worker thread
- Use queue for thread communication
- Handle thread cancellation properly
- Clean up resources on exit

#### Error Handling

```python
try:
    # Risky operation
    result = process_something()
except SpecificError as e:
    self.handle_error(e, "Context message")
except Exception as e:
    self.log_error(f"Unexpected error: {e}")
    messagebox.showerror("Error", "An unexpected error occurred")
```

### Processing Development

#### Adding New Processing Features

1. Add parameter to GUI
2. Pass through ProcessorThread
3. Implement in processing method
4. Add progress reporting
5. Handle cancellation

#### FFmpeg Integration

```python
def new_video_effect(self, input_file: str, output_file: str) -> bool:
    """Apply new video effect."""
    command = [
        'ffmpeg', '-i', input_file,
        '-vf', 'effect_filter',
        output_file
    ]
    return self._run_command(command, log_file)
```

---

## Documentation

### Documentation Requirements

All contributions must include:

1. **Docstrings**: Every function, class, and module
2. **Type Hints**: All parameters and return values
3. **Comments**: Complex logic explained
4. **README Updates**: If adding features
5. **Changelog Entry**: For user-visible changes

### Docstring Format

```python
def function_name(param1: str, param2: int) -> Optional[bool]:
    """
    Brief description of function.
    
    Detailed explanation if needed, including any important
    behaviors, side effects, or considerations.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Optional[bool]: Description of return value,
            None if condition not met
        
    Raises:
        ValueError: When parameters are invalid
        IOError: When file operations fail
        
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
    pass
```

---

## Community

### Communication Channels

- **Issues**: Bug reports and feature requests
- **Discussions**: General questions and ideas
- **Pull Requests**: Code contributions

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on what's best for the community
- Show empathy towards others

### Getting Help

If you need help:
1. Check existing documentation
2. Search closed issues
3. Ask in discussions
4. Create detailed issue

### Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

*Thank you for contributing to PowerHour Video Generator!*  
*Your efforts help make this tool better for everyone.*