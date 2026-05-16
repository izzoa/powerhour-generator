"""
Tests for powerhour/ytdlp_updater.py.

Covers binary discovery, install-method classification, pip-owning-Python
verification, version queries, upgrade-command resolution, and the
YtDlpUpdaterThread queue protocol.
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from powerhour import ytdlp_updater
from powerhour.ytdlp_updater import (
    MANUAL_COMMANDS,
    YtDlpStatus,
    YtDlpUpdaterThread,
    _normalize_path,
    build_manual_upgrade_instructions,
    build_upgrade_command,
    classify_install_method,
    compare_versions,
    find_ytdlp_binary,
    format_check_error,
    query_installed_version,
    query_latest_version,
)


# ---------------------------------------------------------------------------
# Path normalization
# ---------------------------------------------------------------------------

class TestNormalizePath:
    def test_replaces_backslashes_and_casefolds(self):
        assert _normalize_path(
            "C:\\ProgramData\\chocolatey\\bin\\yt-dlp.exe"
        ) == "c:/programdata/chocolatey/bin/yt-dlp.exe"

    def test_lowercase_unix_path_passthrough(self):
        # Already lowercase → casefold is a no-op
        assert _normalize_path("/opt/homebrew/bin/yt-dlp") == "/opt/homebrew/bin/yt-dlp"

    def test_mixed_case_unix_path_casefolds(self):
        # Casefold applies on all platforms (see _normalize_path docstring)
        assert _normalize_path("/usr/local/Cellar/yt-dlp/bin/yt-dlp") == \
            "/usr/local/cellar/yt-dlp/bin/yt-dlp"


# ---------------------------------------------------------------------------
# find_ytdlp_binary / _login_shell_discover
# ---------------------------------------------------------------------------

class TestFindYtdlpBinary:
    def test_present_on_path(self, tmp_path):
        target = tmp_path / "yt-dlp"
        target.write_text("#!/bin/sh\n")
        target.chmod(0o755)
        with patch.object(ytdlp_updater.shutil, "which", return_value=str(target)):
            with patch.object(ytdlp_updater.os.path, "realpath", side_effect=lambda p: p):
                assert find_ytdlp_binary() == str(target)

    def test_missing_returns_none(self):
        with patch.object(ytdlp_updater.shutil, "which", return_value=None):
            with patch.object(ytdlp_updater, "_frozen_app_on_macos", return_value=False):
                assert find_ytdlp_binary() is None

    def test_frozen_macos_uses_login_shell_fallback(self):
        with patch.object(ytdlp_updater.shutil, "which", return_value=None):
            with patch.object(ytdlp_updater, "_frozen_app_on_macos", return_value=True):
                with patch.object(
                    ytdlp_updater, "_login_shell_discover", return_value="/opt/homebrew/bin/yt-dlp"
                ):
                    with patch.object(
                        ytdlp_updater.os.path, "realpath",
                        side_effect=lambda p: p,
                    ):
                        assert find_ytdlp_binary() == "/opt/homebrew/bin/yt-dlp"

    def test_frozen_macos_fallback_returns_empty(self):
        with patch.object(ytdlp_updater.shutil, "which", return_value=None):
            with patch.object(ytdlp_updater, "_frozen_app_on_macos", return_value=True):
                with patch.object(
                    ytdlp_updater, "_login_shell_discover", return_value=None
                ):
                    assert find_ytdlp_binary() is None


class TestLoginShellDiscover:
    @pytest.mark.skipif(sys.platform == "win32", reason="pwd is Unix-only")
    def test_uses_shell_from_env(self):
        fake_pwd = MagicMock()
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}, clear=False):
            with patch.object(
                ytdlp_updater.subprocess, "run",
                return_value=MagicMock(returncode=0, stdout="/opt/homebrew/bin/yt-dlp\n"),
            ) as run_mock:
                result = ytdlp_updater._login_shell_discover("yt-dlp")
                assert result == "/opt/homebrew/bin/yt-dlp"
                argv = run_mock.call_args.args[0]
                assert argv[0] == "/bin/zsh"
                assert argv[1] == "-l"
                assert "command -v yt-dlp" in argv[-1]

    @pytest.mark.skipif(sys.platform == "win32", reason="pwd is Unix-only")
    def test_unknown_shell_falls_back_to_sh(self):
        with patch.dict(os.environ, {"SHELL": "/usr/bin/nu"}, clear=False):
            with patch.object(
                ytdlp_updater.subprocess, "run",
                return_value=MagicMock(returncode=0, stdout="/usr/local/bin/yt-dlp\n"),
            ) as run_mock:
                result = ytdlp_updater._login_shell_discover("yt-dlp")
                assert result == "/usr/local/bin/yt-dlp"
                assert run_mock.call_args.args[0][0] == "/bin/sh"

    @pytest.mark.skipif(sys.platform == "win32", reason="pwd is Unix-only")
    def test_empty_stdout_returns_none(self):
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}, clear=False):
            with patch.object(
                ytdlp_updater.subprocess, "run",
                return_value=MagicMock(returncode=0, stdout=""),
            ):
                assert ytdlp_updater._login_shell_discover("yt-dlp") is None


# ---------------------------------------------------------------------------
# Install-method classification
# ---------------------------------------------------------------------------

class TestClassifyInstallMethod:
    def test_pipx(self):
        m, hint, reason = classify_install_method(
            "/Users/me/.local/pipx/venvs/yt-dlp/bin/yt-dlp"
        )
        assert m == "pipx"
        assert reason is None

    def test_brew_apple_silicon(self):
        m, _, _ = classify_install_method("/opt/homebrew/Cellar/yt-dlp/2024.07.16/bin/yt-dlp")
        assert m == "brew"

    def test_brew_intel(self):
        m, _, _ = classify_install_method("/usr/local/Cellar/yt-dlp/2024.07.16/bin/yt-dlp")
        assert m == "brew"

    def test_choco_normalized(self):
        m, _, _ = classify_install_method("C:\\ProgramData\\chocolatey\\bin\\yt-dlp.exe")
        assert m == "choco"

    def test_distro_usr_bin_unsupported(self):
        m, _, reason = classify_install_method("/usr/bin/yt-dlp")
        assert m == "unsupported"
        assert reason == "apt-or-dnf"

    def test_pyenv_shim_unsupported(self):
        m, _, reason = classify_install_method("/Users/me/.pyenv/shims/yt-dlp")
        assert m == "unsupported"
        assert reason == "pyenv-shim"

    def test_asdf_shim_unsupported(self):
        m, _, reason = classify_install_method("/Users/me/.asdf/shims/yt-dlp")
        assert m == "unsupported"
        assert reason == "asdf-shim"

    def test_mise_shim_unsupported(self):
        m, _, reason = classify_install_method(
            "/Users/me/.local/share/mise/shims/yt-dlp"
        )
        assert m == "unsupported"
        assert reason == "mise-shim"

    def test_nix_store(self):
        m, _, reason = classify_install_method("/nix/store/abcd1234-yt-dlp/bin/yt-dlp")
        assert m == "unsupported"
        assert reason == "nix"

    def test_snap(self):
        m, _, reason = classify_install_method("/snap/yt-dlp/current/bin/yt-dlp")
        assert m == "unsupported"
        assert reason == "snap"

    def test_flatpak(self):
        m, _, reason = classify_install_method(
            "/var/lib/flatpak/exports/bin/yt-dlp"
        )
        assert m == "unsupported"
        assert reason == "flatpak"

    def test_scoop(self):
        m, _, reason = classify_install_method(
            "C:\\Users\\me\\scoop\\apps\\yt-dlp\\current\\yt-dlp.exe"
        )
        assert m == "unsupported"
        assert reason == "scoop"

    def test_winget(self):
        m, _, reason = classify_install_method(
            "C:\\Users\\me\\AppData\\Local\\Microsoft\\WinGet\\Packages\\yt-dlp\\yt-dlp.exe"
        )
        assert m == "unsupported"
        assert reason == "winget"

    def test_npm_global(self):
        m, _, reason = classify_install_method(
            "/usr/local/lib/node_modules/yt-dlp/bin/yt-dlp"
        )
        assert m == "unsupported"
        assert reason == "npm"

    def test_conda_managed_yt_dlp(self, tmp_path):
        """conda-meta/ exists AND contains a yt-dlp-*.json marker → conda."""
        env_dir = tmp_path / "envs" / "foo"
        bin_dir = env_dir / "bin"
        bin_dir.mkdir(parents=True)
        conda_meta = env_dir / "conda-meta"
        conda_meta.mkdir()
        # Conda's package tracking file for yt-dlp:
        (conda_meta / "yt-dlp-2024.07.16-py311_0.json").write_text("{}")
        binary = bin_dir / "yt-dlp"
        binary.write_text("#!" + sys.executable + "\n")
        binary.chmod(0o755)
        m, _, reason = classify_install_method(str(binary))
        assert m == "unsupported"
        assert reason == "conda"

    def test_pip_into_conda_env_falls_through_to_pip(self, tmp_path):
        """conda-meta/ exists but NO yt-dlp-*.json marker → fall through.

        This is the common `pip install yt-dlp` into a conda env case.
        Classifier must NOT short-circuit on conda; the install should be
        handled via the pip path.
        """
        env_dir = tmp_path / "envs" / "foo"
        bin_dir = env_dir / "bin"
        bin_dir.mkdir(parents=True)
        (env_dir / "conda-meta").mkdir()
        # Other conda packages present, but not yt-dlp:
        (env_dir / "conda-meta" / "numpy-1.26.0-py311_0.json").write_text("{}")
        binary = bin_dir / "yt-dlp"
        binary.write_text("#!" + sys.executable + "\n")
        binary.chmod(0o755)
        m, _, reason = classify_install_method(str(binary))
        # Whatever it classifies as, it MUST NOT claim conda owns this binary.
        assert reason != "conda"

    def test_distro_usr_bin_does_not_become_pip_even_with_python_shebang(self, tmp_path):
        # Step 4 (path-pattern unsupported) MUST run before step 6 (pip).
        # We synthesize the realpath check by classifying directly.
        m, _, reason = classify_install_method("/usr/bin/yt-dlp")
        assert m == "unsupported"
        assert reason == "apt-or-dnf"

    def test_standalone_in_user_writable_dir(self, tmp_path):
        binary = tmp_path / "yt-dlp"
        binary.write_text("#!/bin/sh\necho 2024.07.16\n")
        binary.chmod(0o755)
        m, _, _ = classify_install_method(str(binary))
        assert m == "standalone"

    def test_pip_in_venv_classifies_as_pip(self, tmp_path):
        # Build a fake venv layout: <venv>/bin/yt-dlp, <venv>/bin/python3,
        # <venv>/lib/python3.X/site-packages/yt_dlp/__init__.py
        venv = tmp_path / "venv"
        bin_dir = venv / "bin"
        bin_dir.mkdir(parents=True)
        lib_sp = venv / "lib" / "python3.11" / "site-packages" / "yt_dlp"
        lib_sp.mkdir(parents=True)
        (lib_sp / "__init__.py").write_text("")
        python_path = bin_dir / "python3"
        # Use the real python so verify_owning_python's subprocess actually runs.
        os.symlink(sys.executable, str(python_path))
        binary = bin_dir / "yt-dlp"
        binary.write_text(f"#!{python_path}\n")
        binary.chmod(0o755)

        # Patch the verify path to succeed by stubbing the subprocess output.
        fake_output = (
            f"{lib_sp / '__init__.py'}\n"
            f"{python_path}\n"
            f"{venv}\n"
            f"/usr\n"  # base_prefix != prefix → in a venv
        )
        with patch.object(
            ytdlp_updater.subprocess, "run",
            return_value=MagicMock(returncode=0, stdout=fake_output),
        ):
            m, verified, reason = classify_install_method(str(binary))
        assert m == "pip"
        assert verified  # owning_python_hint slot carries verified interpreter
        assert reason is None


# ---------------------------------------------------------------------------
# verify_owning_python
# ---------------------------------------------------------------------------

class TestVerifyOwningPython:
    def test_missing_hint_returns_cannot_verify(self):
        verified, reason = ytdlp_updater.verify_owning_python("/x", "")
        assert verified is None
        assert reason == "cannot-verify-owning-python"

    def test_shim_script_returns_shim_interpreter(self, tmp_path):
        fake_python = tmp_path / "python"
        fake_python.write_text("#!/bin/sh\nexec /real/python \"$@\"\n")
        fake_python.chmod(0o755)
        verified, reason = ytdlp_updater.verify_owning_python(
            "/some/bin/yt-dlp", str(fake_python)
        )
        assert verified is None
        assert reason == "shim-interpreter"

    def test_subprocess_failure_returns_cannot_verify(self):
        with patch.object(ytdlp_updater, "_is_real_interpreter", return_value=True):
            with patch.object(
                ytdlp_updater.os.path, "realpath", side_effect=lambda p: p
            ):
                with patch.object(ytdlp_updater.os.path, "exists", return_value=True):
                    with patch("builtins.open", create=True) as open_mock:
                        open_mock.return_value.__enter__.return_value.read.return_value = b"\x7fELF"
                        with patch.object(
                            ytdlp_updater.subprocess, "run",
                            return_value=MagicMock(returncode=1, stdout=""),
                        ):
                            verified, reason = ytdlp_updater.verify_owning_python(
                                "/x", "/usr/bin/python3"
                            )
                            assert verified is None
                            assert reason == "cannot-verify-owning-python"


# ---------------------------------------------------------------------------
# Version queries and comparator
# ---------------------------------------------------------------------------

class TestQueryInstalledVersion:
    def test_success(self):
        with patch.object(
            ytdlp_updater.subprocess, "run",
            return_value=MagicMock(returncode=0, stdout="2024.07.16\n"),
        ):
            assert query_installed_version("/x/yt-dlp") == ("2024.07.16", None)

    def test_nonzero_exit(self):
        with patch.object(
            ytdlp_updater.subprocess, "run",
            return_value=MagicMock(returncode=2, stdout=""),
        ):
            v, err = query_installed_version("/x/yt-dlp")
            assert v is None
            assert err == "exit_2"

    def test_timeout(self):
        with patch.object(
            ytdlp_updater.subprocess, "run",
            side_effect=subprocess.TimeoutExpired(cmd="yt-dlp", timeout=3),
        ):
            v, err = query_installed_version("/x/yt-dlp")
            assert v is None
            assert err == "timeout"

    def test_oserror(self):
        err = OSError("nope")
        err.errno = 13
        with patch.object(ytdlp_updater.subprocess, "run", side_effect=err):
            v, e = query_installed_version("/x/yt-dlp")
            assert v is None
            assert e == "oserror:13"

    def test_parse_error(self):
        with patch.object(
            ytdlp_updater.subprocess, "run",
            return_value=MagicMock(returncode=0, stdout="not a version\n"),
        ):
            v, err = query_installed_version("/x/yt-dlp")
            assert v is None
            assert err == "parse_error"


class TestQueryLatestVersion:
    def test_success(self):
        payload = json.dumps({"info": {"version": "2024.08.06"}}).encode()
        fake_resp = MagicMock()
        fake_resp.__enter__.return_value.read.return_value = payload
        with patch.object(
            ytdlp_updater.urllib.request, "urlopen", return_value=fake_resp
        ):
            assert query_latest_version() == ("2024.08.06", None)

    def test_http_error(self):
        import urllib.error
        err = urllib.error.HTTPError("u", 503, "boom", {}, None)
        with patch.object(ytdlp_updater.urllib.request, "urlopen", side_effect=err):
            v, e = query_latest_version()
            assert v is None
            assert e == "http_503"

    def test_url_error(self):
        import urllib.error
        with patch.object(
            ytdlp_updater.urllib.request, "urlopen",
            side_effect=urllib.error.URLError("dns"),
        ):
            v, e = query_latest_version()
            assert v is None
            assert e.startswith("url_error:")

    def test_parse_error(self):
        fake_resp = MagicMock()
        fake_resp.__enter__.return_value.read.return_value = b"not json"
        with patch.object(
            ytdlp_updater.urllib.request, "urlopen", return_value=fake_resp
        ):
            v, e = query_latest_version()
            assert v is None
            assert e == "parse_error"


class TestCompareVersions:
    @pytest.mark.parametrize("a,b,expected", [
        ("2024.07.16", "2024.07.16", "current"),
        ("2024.07.16", "2024.08.06", "outdated"),
        ("2023.12.30", "2024.07.16", "outdated"),
        ("2024.07.16.232931", "2024.07.16", "current"),
        ("2024.07.16", "2024.07.16.232931", "outdated"),
        ("v2024.07.16", "2024.07.16", "current"),
        ("V2024.07.16", "v2024.07.16", "current"),
        (None, "2024.07.16", "unknown"),
        ("2024.07.16", None, "unknown"),
        ("master", "2024.07.16", "unknown"),
        ("2024.07.16", "not.a.version", "unknown"),
        ("", "2024.07.16", "unknown"),
    ])
    def test_cases(self, a, b, expected):
        assert compare_versions(a, b) == expected


class TestFormatCheckError:
    def test_both_none(self):
        assert format_check_error(None, None) is None

    def test_only_installed(self):
        assert format_check_error("timeout", None) == "installed: timeout"

    def test_only_latest(self):
        assert format_check_error(None, "http_503") == "latest: http_503"

    def test_both(self):
        assert format_check_error("timeout", "http_503") == "installed: timeout; latest: http_503"


# ---------------------------------------------------------------------------
# Upgrade command resolution
# ---------------------------------------------------------------------------

class TestBuildUpgradeCommand:
    def _status(self, method, **overrides):
        defaults = dict(
            installed_version="2024.07.16",
            latest_version="2024.08.06",
            install_method=method,
            freshness="outdated",
            binary_path="/usr/local/bin/yt-dlp",
            owning_python="/x/venv/bin/python",
            check_error=None,
            unsupported_reason=None,
            manual_command=None,
        )
        defaults.update(overrides)
        return YtDlpStatus(**defaults)

    def test_brew_uses_absolute_path(self):
        with patch.object(
            ytdlp_updater, "find_package_manager_binary",
            return_value="/opt/homebrew/bin/brew",
        ):
            argv = build_upgrade_command(self._status("brew"))
        assert argv == ["/opt/homebrew/bin/brew", "upgrade", "yt-dlp"]

    def test_pipx_uses_absolute_path(self):
        with patch.object(
            ytdlp_updater, "find_package_manager_binary",
            return_value="/Users/me/.local/bin/pipx",
        ):
            argv = build_upgrade_command(self._status("pipx"))
        assert argv == ["/Users/me/.local/bin/pipx", "upgrade", "yt-dlp"]

    def test_choco(self):
        with patch.object(
            ytdlp_updater, "find_package_manager_binary",
            return_value="C:\\ProgramData\\chocolatey\\bin\\choco.exe",
        ):
            argv = build_upgrade_command(self._status("choco"))
        assert argv == [
            "C:\\ProgramData\\chocolatey\\bin\\choco.exe", "upgrade", "yt-dlp", "-y"
        ]

    def test_pip_with_owning_python(self):
        argv = build_upgrade_command(self._status("pip"))
        assert argv == ["/x/venv/bin/python", "-m", "pip", "install", "-U", "yt-dlp"]

    def test_standalone(self):
        argv = build_upgrade_command(self._status("standalone"))
        assert argv == ["/usr/local/bin/yt-dlp", "-U"]

    def test_unsupported_conda_returns_conda_argv(self):
        with patch.object(
            ytdlp_updater, "find_package_manager_binary",
            return_value="/opt/anaconda3/bin/conda",
        ):
            argv = build_upgrade_command(
                self._status("unsupported", unsupported_reason="conda")
            )
        assert argv == [
            "/opt/anaconda3/bin/conda", "update", "-y", "-c", "conda-forge", "yt-dlp"
        ]

    def test_unsupported_pyenv_returns_pyenv_argv(self):
        with patch.object(
            ytdlp_updater, "find_package_manager_binary",
            return_value="/Users/me/.pyenv/bin/pyenv",
        ):
            argv = build_upgrade_command(
                self._status("unsupported", unsupported_reason="pyenv-shim")
            )
        assert argv == [
            "/Users/me/.pyenv/bin/pyenv", "exec", "pip", "install", "--upgrade", "yt-dlp"
        ]

    def test_unsupported_winget_returns_winget_argv(self):
        with patch.object(
            ytdlp_updater, "find_package_manager_binary",
            return_value="C:\\Users\\me\\winget.exe",
        ):
            argv = build_upgrade_command(
                self._status("unsupported", unsupported_reason="winget")
            )
        assert argv == [
            "C:\\Users\\me\\winget.exe", "upgrade", "yt-dlp",
            "--silent", "--accept-source-agreements",
        ]

    @pytest.mark.parametrize("reason", ["apt-or-dnf", "snap", "nix", "unknown"])
    def test_unsupported_sudo_or_immutable_returns_none(self, reason):
        # apt/dnf/snap need sudo; nix is immutable; unknown has no command.
        # These fall back to manual-command-in-log behavior.
        assert build_upgrade_command(
            self._status("unsupported", unsupported_reason=reason)
        ) is None

    def test_unsupported_conda_without_conda_binary_returns_none(self):
        with patch.object(
            ytdlp_updater, "find_package_manager_binary", return_value=None
        ):
            assert build_upgrade_command(
                self._status("unsupported", unsupported_reason="conda")
            ) is None

    def test_missing_returns_none(self):
        assert build_upgrade_command(self._status("missing", owning_python=None)) is None

    def test_brew_without_brew_binary_returns_none(self):
        with patch.object(
            ytdlp_updater, "find_package_manager_binary", return_value=None
        ):
            assert build_upgrade_command(self._status("brew")) is None


class TestBuildManualUpgradeInstructions:
    @pytest.mark.parametrize("reason", list(MANUAL_COMMANDS.keys()))
    def test_known_reasons_have_commands(self, reason):
        s = YtDlpStatus(
            installed_version=None,
            latest_version=None,
            install_method="unsupported",
            freshness="outdated",
            binary_path=None,
            owning_python=None,
            check_error=None,
            unsupported_reason=reason,
            manual_command=None,
        )
        assert build_manual_upgrade_instructions(s) == MANUAL_COMMANDS[reason]

    def test_unrecognized_reason_falls_back_to_unknown(self):
        s = YtDlpStatus(
            installed_version=None,
            latest_version=None,
            install_method="unsupported",
            freshness="outdated",
            binary_path=None,
            owning_python=None,
            check_error=None,
            unsupported_reason="totally-novel-manager",
            manual_command=None,
        )
        assert build_manual_upgrade_instructions(s) == MANUAL_COMMANDS["unknown"]


# ---------------------------------------------------------------------------
# Worker thread queue protocol
# ---------------------------------------------------------------------------

DISALLOWED_TYPES = {"error", "status", "progress", "video_progress", "complete"}


def _drain(q: queue.Queue, timeout: float = 5.0) -> List[dict]:
    out = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            out.append(q.get(timeout=0.1))
        except queue.Empty:
            break
    return out


def _run_thread(mode: str) -> List[dict]:
    q = queue.Queue()
    t = YtDlpUpdaterThread(q, mode=mode)  # type: ignore[arg-type]
    t.start()
    t.join(timeout=10)
    return _drain(q)


class TestUpdaterQueueProtocol:
    def _patch_pipeline(
        self,
        binary_path: str = "/x/bin/yt-dlp",
        method: str = "standalone",
        installed: str = "2024.07.16",
        latest: str = "2024.07.16",
        unsupported_reason=None,
    ):
        return [
            patch.object(ytdlp_updater, "find_ytdlp_binary", return_value=binary_path),
            patch.object(
                ytdlp_updater, "classify_install_method",
                return_value=(method, None, unsupported_reason),
            ),
            patch.object(
                ytdlp_updater, "query_installed_version", return_value=(installed, None)
            ),
            patch.object(
                ytdlp_updater, "query_latest_version", return_value=(latest, None)
            ),
        ]

    def test_check_only_emits_only_status(self):
        with self._patch_pipeline()[0], self._patch_pipeline()[1], \
             self._patch_pipeline()[2], self._patch_pipeline()[3]:
            msgs = _run_thread("check_only")
        types = [m["type"] for m in msgs]
        assert "ytdlp_status" in types
        assert not (set(types) & DISALLOWED_TYPES)

    def test_missing_emits_one_status(self):
        with patch.object(ytdlp_updater, "find_ytdlp_binary", return_value=None):
            msgs = _run_thread("check_only")
        status_msgs = [m for m in msgs if m["type"] == "ytdlp_status"]
        assert len(status_msgs) == 1
        assert status_msgs[0]["install_method"] == "missing"
        assert status_msgs[0]["freshness"] == "missing"
        assert not (set(m["type"] for m in msgs) & DISALLOWED_TYPES)

    def test_check_and_upgrade_when_current_emits_complete_success(self):
        with patch.object(
            ytdlp_updater, "find_ytdlp_binary", return_value="/x/bin/yt-dlp"
        ), patch.object(
            ytdlp_updater, "classify_install_method",
            return_value=("standalone", None, None),
        ), patch.object(
            ytdlp_updater, "query_installed_version", return_value=("2024.07.16", None)
        ), patch.object(
            ytdlp_updater, "query_latest_version", return_value=("2024.07.16", None)
        ):
            msgs = _run_thread("check_and_upgrade")

        types = [m["type"] for m in msgs]
        assert "ytdlp_status" in types
        completes = [m for m in msgs if m["type"] == "ytdlp_update_complete"]
        assert len(completes) == 1
        assert completes[0]["success"] is True
        assert completes[0]["reverified_freshness"] == "current"
        # And the "already up to date" log line
        logs = [m for m in msgs if m["type"] == "log"]
        assert any("already up to date" in m["message"] for m in logs)
        assert not (set(types) & DISALLOWED_TYPES)

    def test_check_and_upgrade_when_unknown_emits_complete_failure(self):
        with patch.object(
            ytdlp_updater, "find_ytdlp_binary", return_value="/x/bin/yt-dlp"
        ), patch.object(
            ytdlp_updater, "classify_install_method",
            return_value=("standalone", None, None),
        ), patch.object(
            ytdlp_updater, "query_installed_version", return_value=(None, "parse_error")
        ), patch.object(
            ytdlp_updater, "query_latest_version", return_value=("2024.07.16", None)
        ):
            msgs = _run_thread("check_and_upgrade")

        completes = [m for m in msgs if m["type"] == "ytdlp_update_complete"]
        assert len(completes) == 1
        assert completes[0]["success"] is False
        assert completes[0]["exit_code"] == -3
        assert not (set(m["type"] for m in msgs) & DISALLOWED_TYPES)

    def test_check_and_upgrade_outdated_unsupported_emits_complete_minus_two(self):
        with patch.object(
            ytdlp_updater, "find_ytdlp_binary", return_value="/usr/bin/yt-dlp"
        ), patch.object(
            ytdlp_updater, "classify_install_method",
            return_value=("unsupported", None, "apt-or-dnf"),
        ), patch.object(
            ytdlp_updater, "query_installed_version", return_value=("2024.06.01", None)
        ), patch.object(
            ytdlp_updater, "query_latest_version", return_value=("2024.07.16", None)
        ):
            msgs = _run_thread("check_and_upgrade")

        completes = [m for m in msgs if m["type"] == "ytdlp_update_complete"]
        assert len(completes) == 1
        assert completes[0]["success"] is False
        assert completes[0]["exit_code"] == -2
        # The manual command must appear in the log
        assert any(
            "apt" in m["message"].lower()
            for m in msgs if m["type"] == "log"
        )

    def test_check_and_upgrade_success_with_reverification_current(self):
        # Outdated → run subprocess (mocked exit 0 with one WARNING:) → re-verify current
        fake_proc = MagicMock()
        fake_proc.stdout = iter([
            "Downloading https://...\n",
            "WARNING: minor issue\n",
            "Successfully installed yt-dlp-2024.08.06\n",
        ])
        fake_proc.wait.return_value = None
        fake_proc.returncode = 0

        # find_ytdlp_binary called twice: initial discovery and re-verify.
        # query_installed_version called twice: pre and post upgrade.
        find_seq = iter(["/x/bin/yt-dlp", "/x/bin/yt-dlp"])
        installed_seq = iter([("2024.07.01", None), ("2024.08.06", None)])

        with patch.object(
            ytdlp_updater, "find_ytdlp_binary", side_effect=lambda: next(find_seq)
        ), patch.object(
            ytdlp_updater, "classify_install_method",
            return_value=("standalone", None, None),
        ), patch.object(
            ytdlp_updater, "query_installed_version",
            side_effect=lambda *_a, **_kw: next(installed_seq),
        ), patch.object(
            ytdlp_updater, "query_latest_version", return_value=("2024.08.06", None)
        ), patch.object(
            ytdlp_updater, "build_upgrade_command",
            return_value=["/x/bin/yt-dlp", "-U"],
        ), patch.object(
            ytdlp_updater.subprocess, "Popen", return_value=fake_proc
        ):
            msgs = _run_thread("check_and_upgrade")

        completes = [m for m in msgs if m["type"] == "ytdlp_update_complete"]
        assert len(completes) == 1
        assert completes[0]["success"] is True
        assert completes[0]["reverified_freshness"] == "current"
        assert completes[0]["latest_version"] == "2024.08.06"
        # Level routing for WARNING:
        warnings = [m for m in msgs if m["type"] == "log" and m["level"] == "warning"]
        assert any("WARNING:" in m["message"] for m in warnings)

    def test_check_and_upgrade_success_but_still_outdated(self):
        # Subprocess exits 0 but post-upgrade query returns the same older version.
        fake_proc = MagicMock()
        fake_proc.stdout = iter(["yt-dlp is already the newest version\n"])
        fake_proc.wait.return_value = None
        fake_proc.returncode = 0

        find_seq = iter(["/x/bin/yt-dlp", "/x/bin/yt-dlp"])
        # Pre and post upgrade both return the same older version.
        installed_seq = iter([("2024.07.01", None), ("2024.07.01", None)])

        with patch.object(
            ytdlp_updater, "find_ytdlp_binary", side_effect=lambda: next(find_seq)
        ), patch.object(
            ytdlp_updater, "classify_install_method",
            return_value=("brew", None, None),
        ), patch.object(
            ytdlp_updater, "query_installed_version",
            side_effect=lambda *_a, **_kw: next(installed_seq),
        ), patch.object(
            ytdlp_updater, "query_latest_version", return_value=("2024.08.06", None)
        ), patch.object(
            ytdlp_updater, "build_upgrade_command",
            return_value=["/opt/homebrew/bin/brew", "upgrade", "yt-dlp"],
        ), patch.object(
            ytdlp_updater.subprocess, "Popen", return_value=fake_proc
        ):
            msgs = _run_thread("check_and_upgrade")

        completes = [m for m in msgs if m["type"] == "ytdlp_update_complete"]
        assert len(completes) == 1
        assert completes[0]["success"] is True
        assert completes[0]["reverified_freshness"] == "outdated"
        assert completes[0]["new_version"] == "2024.07.01"
        assert completes[0]["latest_version"] == "2024.08.06"
        # Warning log that both versions were mentioned
        warns = [m for m in msgs if m["type"] == "log" and m["level"] == "warning"]
        assert any(
            "2024.07.01" in m["message"] and "2024.08.06" in m["message"]
            for m in warns
        )


# ---------------------------------------------------------------------------
# GUI smoke test (skipped when no display is available)
# ---------------------------------------------------------------------------

def _can_create_tk():
    if sys.platform != "darwin" and not os.environ.get("DISPLAY"):
        return False
    try:
        import tkinter
        root = tkinter.Tk()
        root.destroy()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _can_create_tk(), reason="No display available for Tkinter")
class TestGuiSmoke:
    def test_status_bar_widgets_exist_and_legacy_preserved(self):
        # Stub the updater thread so the launch-time check doesn't run real network.
        with patch.object(ytdlp_updater, "YtDlpUpdaterThread") as fake_thread:
            fake_thread.return_value.start = MagicMock()
            from powerhour.powerhour_gui import PowerHourGUI
            gui = PowerHourGUI()
            try:
                # New widgets
                assert hasattr(gui, "ytdlp_version_label")
                assert hasattr(gui, "ytdlp_freshness_label")
                assert hasattr(gui, "ytdlp_action_button")
                # Pre-existing widgets preserved
                assert hasattr(gui, "hint_label")
                assert hasattr(gui, "operation_label")
                assert hasattr(gui, "resource_label")
                # State flags initialized
                assert gui._ytdlp_status is None
                assert gui._ytdlp_update_in_progress is False
                assert gui._processing_active is False
            finally:
                gui.destroy()


# ---------------------------------------------------------------------------
# Race-safe re-enable test
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _can_create_tk(), reason="No display available for Tkinter")
class TestRaceSafeReenable:
    def test_processing_end_leaves_button_disabled_while_updater_active(self):
        with patch.object(ytdlp_updater, "YtDlpUpdaterThread") as fake_thread:
            fake_thread.return_value.start = MagicMock()
            from powerhour.powerhour_gui import PowerHourGUI
            gui = PowerHourGUI()
            try:
                # Seed a status so the enable gate has something to check
                gui._handle_ytdlp_status({
                    "type": "ytdlp_status",
                    "installed_version": "2024.07.16",
                    "latest_version": "2024.07.16",
                    "install_method": "standalone",
                    "freshness": "current",
                    "binary_path": "/x/yt-dlp",
                    "owning_python": None,
                    "check_error": None,
                    "unsupported_reason": None,
                    "manual_command": None,
                })
                # Simulate: processing job starts, then updater click
                gui._processing_active = True
                gui._ytdlp_update_in_progress = True
                gui.ytdlp_action_button.config(state="disabled")
                # Processing ends first
                gui.reset_ui_state()
                assert str(gui.ytdlp_action_button["state"]) == "disabled", \
                    "Button must stay disabled while updater is still running"
                # Updater completes
                gui._handle_ytdlp_update_complete({
                    "type": "ytdlp_update_complete",
                    "success": True,
                    "exit_code": 0,
                    "new_version": "2024.07.16",
                    "latest_version": "2024.07.16",
                    "reverified_freshness": "current",
                })
                assert str(gui.ytdlp_action_button["state"]) == "normal"
            finally:
                gui.destroy()
