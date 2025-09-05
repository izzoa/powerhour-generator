# Release Guide for PowerHour Generator

## Version 1.0.0

### 🎉 Release Overview

PowerHour Generator v1.0.0 marks the first official release with the introduction of a full-featured GUI application alongside the original CLI tool. This release transforms the user experience while maintaining backward compatibility.

### 📋 Pre-Release Checklist

Before creating a release, ensure:

- [ ] All tests pass (`make test`)
- [ ] Code is linted and formatted (`make lint format`)
- [ ] Documentation is up to date
- [ ] Version numbers updated in:
  - [ ] `setup.py`
  - [ ] `powerhour.spec`
  - [ ] `CHANGELOG.md`
  - [ ] `Makefile`
- [ ] Dependencies are minimal and documented
- [ ] FFmpeg installation instructions are clear

### 🔨 Building Releases

#### Quick Build (All Platforms)

```bash
# Clean, test, and build
make clean test build release
```

#### Platform-Specific Builds

##### Windows
```bash
# Using PowerShell or Git Bash
python build.py --platform windows --clean --release
```

##### macOS
```bash
# Build app bundle
python build.py --platform macos --clean --release
```

##### Linux
```bash
# Build AppImage or tar.gz
python build.py --platform linux --clean --release
```

#### Python Package
```bash
# Build wheel and source distribution
make build-wheel build-source
```

### 📦 Release Artifacts

Each release should include:

1. **Executable Packages**
   - Windows: `PowerHourGenerator-1.0.0-windows.zip`
   - macOS: `PowerHourGenerator-1.0.0-macos.tar.gz`
   - Linux: `PowerHourGenerator-1.0.0-linux.tar.gz`

2. **Python Packages**
   - Wheel: `powerhour_generator-1.0.0-py3-none-any.whl`
   - Source: `powerhour-generator-1.0.0.tar.gz`

3. **Documentation Bundle**
   - All markdown documentation files
   - Quick start guides
   - API documentation (if applicable)

### 🚀 Release Process

#### 1. Final Testing

```bash
# Run comprehensive tests
make clean
make install-dev
make test
make lint
```

#### 2. Build All Distributions

```bash
# Build everything
make build-all
python build.py --type all --release
```

#### 3. Test Installations

```bash
# Test pip installation
pip install dist/powerhour_generator-*.whl
powerhour-gui  # Test GUI
powerhour --help  # Test CLI

# Test executable
cd releases/PowerHourGenerator-*/
./PowerHourGenerator  # Linux/macOS
# or
PowerHourGenerator.exe  # Windows
```

#### 4. Create GitHub Release

1. Tag the release:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. Create release on GitHub:
   - Go to https://github.com/izzoa/powerhour-generator/releases
   - Click "Create a new release"
   - Select the tag `v1.0.0`
   - Title: "PowerHour Generator v1.0.0 - GUI Release"
   - Upload all artifacts from `releases/` directory

3. Write release notes (template below)

#### 5. Publish to PyPI (Optional)

```bash
# Upload to Test PyPI first
make upload-test

# Test installation from Test PyPI
pip install -i https://test.pypi.org/simple/ powerhour-generator

# If successful, upload to PyPI
make upload-pypi
```

### 📝 Release Notes Template

```markdown
# PowerHour Generator v1.0.0

## 🎉 What's New

### GUI Application
- Brand new graphical user interface built with Tkinter
- Real-time progress tracking and visualization
- Drag-and-drop file selection
- Configuration persistence
- Professional threading architecture

### Features
- ✅ 60-minute video compilation from folder or YouTube
- ✅ Automatic audio normalization
- ✅ Customizable fade transitions
- ✅ Common clip insertion between segments
- ✅ Cross-platform compatibility

## 📥 Installation

### Quick Start (Executable)
Download the appropriate package for your platform and extract.

### Python Package
```bash
pip install powerhour-generator
```

### Requirements
- Python 3.8+
- FFmpeg and FFprobe
- Optional: yt-dlp for YouTube support

## 🚀 Usage

### GUI Mode
```bash
powerhour-gui
# or run the executable directly
```

### CLI Mode (Legacy)
```bash
powerhour --input /path/to/videos --output result.mp4
```

## 🐛 Bug Fixes
- Fixed memory leak in video processing
- Improved error handling for corrupt files
- Better cleanup of temporary files

## 💔 Breaking Changes
None - Full backward compatibility maintained

## 📚 Documentation
- [User Guide](USER_GUIDE.md)
- [GUI Quick Start](README_GUI.md)
- [Architecture](ARCHITECTURE.md)

## 🙏 Acknowledgments
Thanks to all contributors and testers!

## 📋 Known Issues
- Large video sets (>100GB) may require significant disk space
- Some exotic codecs may not be supported

## 🔮 Next Release Preview
- Batch processing queue
- Video preview thumbnails
- Dark mode theme
```

### 🧪 Post-Release Testing

After release, verify:

1. **Download Testing**
   - Download from GitHub releases
   - Verify checksums (if provided)
   - Test on clean system

2. **Installation Testing**
   ```bash
   # Test pip installation
   pip install powerhour-generator
   
   # Test executable
   ./PowerHourGenerator --version
   ```

3. **Functionality Testing**
   - Process small test set (3-5 videos)
   - Process full set (60 videos)
   - Test cancellation
   - Verify output quality

### 🔄 Rollback Plan

If critical issues are found:

1. Mark release as pre-release on GitHub
2. Yank package from PyPI: `pip install twine && twine yank powerhour-generator==1.0.0`
3. Document issues in hotfix branch
4. Release patch version (1.0.1) with fixes

### 📊 Success Metrics

Track release success:

- GitHub release downloads
- PyPI download statistics
- Issue reports (aim for <5 critical in first week)
- User feedback on improvements

### 🛠️ Maintenance

Post-release maintenance:

1. **Monitor Issues**
   - Check GitHub issues daily for first week
   - Respond to user questions
   - Track common problems

2. **Patch Releases**
   - Critical fixes: Release immediately (1.0.1)
   - Minor fixes: Bundle for next release (1.1.0)
   
3. **Documentation Updates**
   - Update FAQ based on user questions
   - Improve unclear sections
   - Add troubleshooting guides

### 📅 Release Schedule

- **Major Releases (X.0.0)**: Annually
- **Minor Releases (X.Y.0)**: Quarterly
- **Patch Releases (X.Y.Z)**: As needed

### 🔐 Security

For security issues:
1. Do not create public issue
2. Email security@powerhour-generator.com
3. Follow responsible disclosure
4. Release security patch immediately

---

**Last Updated**: September 2025  
**Maintainer**: Anthony Izzo
**Contact**: anthony@izzo.one