# Release Procedure

Maintainer-only guide for cutting a release of PowerHour Generator. Intentionally version-agnostic; substitute your target version (e.g., `1.2.0`) wherever you see `<version>`.

## Pre-release checklist

- [ ] `make ci` is green (clean install, tests, lint, build all succeed).
- [ ] `docs/CHANGELOG.md` has a `[Unreleased]` section with the changes about to ship. Roll it into a `## [<version>] - YYYY-MM-DD` heading.
- [ ] `powerhour/__init__.py:__version__` is bumped to `<version>`. Everything else (`setup.py`, `scripts/build.py`, `powerhour.spec`, `Makefile`) derives from this — nothing else needs editing.
- [ ] `README.md` reflects any user-visible changes (per [CLAUDE.md § Keeping documentation in sync](../CLAUDE.md#keeping-documentation-in-sync) thresholds).
- [ ] Any in-flight OpenSpec changes for the release are archived (`openspec archive <change-name>`).

## Build

```bash
# Clean, install, test, build everything
make clean
make install-dev
make ci                  # runs install, test, lint, build
make build-all           # exe + wheel + source
```

For platform-specific builds (must run on the target OS — no cross-compilation):

```bash
python scripts/build.py --platform windows --clean --release
python scripts/build.py --platform macos --clean --release
python scripts/build.py --platform linux --clean --release
```

Outputs land in `dist/` (PyInstaller) and `releases/` (zipped/tar'd release packages).

## Release artifacts

Each release should include:

- **Executable bundles** — one per OS, produced by `make build-exe` + `scripts/build.py --release`:
  - `PowerHourGenerator-<version>-windows.zip`
  - `PowerHourGenerator-<version>-macos.tar.gz`
  - `PowerHourGenerator-<version>-linux.tar.gz`
- **Python packages** — produced by `make build-wheel` + `make build-source`:
  - `powerhour_generator-<version>-py3-none-any.whl`
  - `powerhour-generator-<version>.tar.gz`
- **Documentation bundle** — `README.md` + everything in `docs/` is included automatically by `scripts/build.py` in each release zip/tarball.

## Smoke-test before tagging

```bash
# Test pip installation
pip install dist/powerhour_generator-*.whl
powerhour-gui            # confirms GUI entry point works
powerhour --help         # confirms CLI entry point works
pip uninstall powerhour-generator

# Test executable on a clean shell
cd releases/PowerHourGenerator-<version>-<platform>/
./PowerHourGenerator     # Linux/macOS
PowerHourGenerator.exe   # Windows
```

On macOS, verify the `.app` bundle works when launched from Finder (this exercises the [frozen-`.app` PATH gap fallback](../CLAUDE.md#macos-frozen-app-path-gap) in the yt-dlp updater).

## Tag and push

```bash
git tag -a v<version> -m "Release version <version>"
git push origin v<version>
```

## Create the GitHub release

1. Visit https://github.com/izzoa/powerhour-generator/releases and click "Create a new release."
2. Select tag `v<version>`.
3. Title: `PowerHour Generator v<version>`.
4. Body: copy from the matching `## [<version>]` block in `docs/CHANGELOG.md`. The CI workflow at `.github/workflows/release.yml` may produce a draft for you.
5. Upload all artifacts from `releases/` and `dist/`.
6. Publish.

## Publish to PyPI

```bash
# Upload to Test PyPI first
make upload-test

# Verify install from Test PyPI
pip install -i https://test.pypi.org/simple/ powerhour-generator==<version>

# Publish to real PyPI
make upload-pypi
```

## Post-release verification

- [ ] Download the GitHub release artifacts and confirm checksums (if attached) match.
- [ ] `pip install powerhour-generator==<version>` on a clean venv succeeds.
- [ ] Run the GUI against a small test set (3–5 videos) to confirm processing still works end-to-end.
- [ ] Watch GitHub Issues for the first 24 hours.

## Hotfix / rollback

If a critical bug ships:

1. Mark the GitHub release as a pre-release while you investigate.
2. Yank the affected PyPI version: `twine yank powerhour-generator -v <version> -m "<reason>"`.
3. Branch from `main`, apply the fix, bump `__version__` to a patch release (e.g., `<version>+1.patch`), update `CHANGELOG.md`, and re-run this entire procedure.

Never delete a published GitHub release or PyPI version — yank, don't delete; the package index records depend on version numbers being stable.

## Release cadence

There's no fixed schedule. Cut a release when:

- A user-visible feature lands.
- A behavior bug or security issue is fixed.
- Enough internal changes have accumulated that the version-sync metadata is meaningfully stale.

Patch releases for fixes; minor releases for additive features; major releases for breaking changes (license change, removed CLI behavior, removed config keys, etc.).
