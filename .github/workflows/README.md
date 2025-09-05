# GitHub Actions Workflows

This directory contains automated workflows for building, testing, and releasing PowerHour Generator.

## Workflows

### 🚀 release.yml - Release Build & Distribution
**Trigger**: On version tags (`v*`) or manual dispatch
**Purpose**: Creates production installers for all platforms

**Outputs**:
- **Windows**: `.msi` installer with WiX Toolset
- **Linux**: `.deb` package for Debian/Ubuntu with logo.png icon
- **macOS**: `.dmg` disk image with app bundle and logo.png icon

**Features**:
- Automatic GitHub release creation
- Cross-platform parallel builds
- Installer generation with proper metadata
- Release notes generation
- Uses logo.png as application icon

**Usage**:
```bash
# Create a version tag to trigger release
git tag v1.0
git push origin v1.0

# Or manually trigger via GitHub Actions UI
```

### 🧪 ci.yml - Continuous Integration
**Trigger**: Push to main/develop, pull requests, manual dispatch
**Purpose**: Test builds across multiple Python versions and platforms

**Matrix Testing**:
- **Operating Systems**: Ubuntu, Windows, macOS
- **Python Versions**: 3.8, 3.9, 3.10, 3.11

**Checks**:
- Code linting (flake8)
- Type checking (mypy)
- Unit tests (pytest)
- Import tests
- PyInstaller build test
- Code coverage reporting

## Secrets Required

No secrets are required for basic operation. However, for enhanced features:

- **GITHUB_TOKEN**: Automatically provided by GitHub Actions
- **CODECOV_TOKEN**: (Optional) For code coverage reporting
- **SIGNING_CERTIFICATE**: (Optional) For code signing on macOS/Windows

## Local Testing

You can test workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash  # Linux

# Test CI workflow
act push

# Test release workflow
act release --tag v1.0

# Test specific job
act -j build-windows
```

## Build Matrix

| Platform | Python | Installer Type | Size (approx) |
|----------|--------|---------------|---------------|
| Windows  | 3.10   | MSI           | ~25 MB        |
| Linux    | 3.10   | DEB           | ~20 MB        |
| macOS    | 3.10   | DMG           | ~30 MB        |

## Workflow Badges

Add these badges to your README:

```markdown
![Release](https://github.com/izzoa/powerhour-generator/actions/workflows/release.yml/badge.svg)
![CI](https://github.com/izzoa/powerhour-generator/actions/workflows/ci.yml/badge.svg)
```

## Troubleshooting

### Windows MSI Build Fails
- Ensure WiX Toolset paths are correct
- Check Windows-specific file paths use backslashes

### Linux DEB Build Fails
- Verify all Debian control file fields
- Ensure proper file permissions (especially for executables)

### macOS DMG Build Fails
- Check if `create-dmg` is installed
- Verify app bundle structure
- Ensure Info.plist is valid XML

### PyInstaller Issues
- Clear PyInstaller cache: `pyinstaller --clean`
- Check for missing hidden imports
- Verify all dependencies are installed

## Maintenance

### Updating Python Version
1. Update `PYTHON_VERSION` in workflow env
2. Update matrix versions in ci.yml
3. Test builds locally first

### Adding New Platforms
1. Add new matrix entry
2. Create platform-specific build steps
3. Update installer creation logic
4. Test on target platform

### Dependency Updates
- Review and update requirements*.txt regularly
- Test with new dependency versions in CI first
- Update PyInstaller version for compatibility

## Release Process

1. **Prepare Release**:
   ```bash
   # Update version in files
   # Update CHANGELOG.md
   git commit -m "Prepare release v1.0"
   ```

2. **Create Tag**:
   ```bash
   git tag -a v1.0 -m "Release version 1.0"
   git push origin main
   git push origin v1.0
   ```

3. **Monitor Workflow**:
   - Check Actions tab on GitHub
   - Wait for all platform builds to complete
   - Verify release is created with all artifacts

4. **Post-Release**:
   - Test downloaded installers
   - Update documentation if needed
   - Announce release

## Best Practices

1. **Always test locally first** using act or manual builds
2. **Keep workflows DRY** - use composite actions for repeated steps
3. **Pin action versions** for reproducibility
4. **Cache dependencies** to speed up builds
5. **Use matrix strategy** for parallel builds
6. **Set reasonable timeouts** to prevent hanging builds
7. **Include app icon** (logo.png) in builds

## Contributing

When modifying workflows:
1. Test changes in a feature branch
2. Use workflow_dispatch for manual testing
3. Verify all matrix combinations pass
4. Update this README if adding new workflows

## Support

For workflow issues:
- Check GitHub Actions status: https://www.githubstatus.com/
- Review workflow logs in Actions tab
- Open an issue with workflow logs attached