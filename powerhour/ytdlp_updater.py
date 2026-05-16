"""
yt-dlp version management and in-app updater for the PowerHour GUI.

Provides binary discovery, install-method classification, version queries
against PyPI, and a worker thread that streams upgrade output into the GUI's
existing message queue using namespaced message types.

The updater thread emits ONLY: `ytdlp_status`, `ytdlp_update_complete`, and
the existing `log` type. It MUST NOT emit `error`, `status`, `progress`,
`video_progress`, or `complete` — those belong to ProcessorThread and trigger
destructive UI handlers.

See openspec/changes/add-yt-dlp-update-check/design.md for the rationale
behind classification ordering and pip-owning-Python verification.
"""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from typing import Literal, Optional

try:
    import pwd  # Unix only
except ImportError:
    pwd = None  # type: ignore[assignment]

from powerhour import __version__


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

InstallMethod = Literal[
    'pipx', 'brew', 'choco', 'unsupported', 'pip', 'standalone', 'missing'
]
Freshness = Literal['current', 'outdated', 'unknown', 'missing']


@dataclass
class YtDlpStatus:
    installed_version: Optional[str]
    latest_version: Optional[str]
    install_method: InstallMethod
    freshness: Freshness
    binary_path: Optional[str]
    owning_python: Optional[str]
    check_error: Optional[str]
    unsupported_reason: Optional[str]
    manual_command: Optional[str]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"
PYPI_TIMEOUT = 5.0
DISCOVERY_TIMEOUT = 3.0
INSTALLED_VERSION_TIMEOUT = 3.0
PYTHON_VERIFY_TIMEOUT = 5.0
USER_AGENT = f"PowerHour-Generator/{__version__}"

# Stable destination for the "How to install" button when yt-dlp is missing.
# Points at the project README anchor; the README must include the matching anchor.
YTDLP_INSTALL_DOCS_URL = "https://github.com/izzoa/powerhour-generator#yt-dlp"

# Login-shell allowlist for frozen-.app PATH discovery on macOS.
_SHELL_ALLOWLIST = {
    '/bin/zsh', '/bin/bash',
    '/usr/local/bin/fish', '/opt/homebrew/bin/fish',
    '/bin/sh',
}
_FALLBACK_SHELL = '/bin/sh'

# Path-pattern unsupported managers (ordered, first-match wins within the
# unsupported step). Each tuple is (substring_or_prefix_marker, reason_tag).
_PATH_UNSUPPORTED_PATTERNS = [
    ('/nix/store/', 'nix'),
    ('/snap/', 'snap'),
    ('/var/lib/flatpak/', 'flatpak'),
    ('/.pyenv/shims/', 'pyenv-shim'),
    ('/.asdf/shims/', 'asdf-shim'),
    ('/.local/share/mise/shims/', 'mise-shim'),
    ('/scoop/', 'scoop'),
    ('/microsoft/winget/', 'winget'),
    ('/lib/node_modules/', 'npm'),
]

# Distro-installed binaries live in /usr/bin or /usr/sbin on Debian/Fedora/etc.
_DISTRO_PREFIXES = ('/usr/bin/', '/usr/sbin/')

# Manual upgrade commands shown when auto-upgrade is not available.
MANUAL_COMMANDS = {
    'conda': 'conda update -c conda-forge yt-dlp',
    'apt-or-dnf': (
        'sudo apt update && sudo apt install --only-upgrade yt-dlp   '
        '# Debian/Ubuntu; on Fedora use: sudo dnf upgrade yt-dlp'
    ),
    'pyenv-shim': 'pyenv exec pip install --upgrade yt-dlp',
    'asdf-shim': 'asdf reshim && pip install --upgrade yt-dlp   # via the active asdf Python',
    'mise-shim': 'mise exec -- pip install --upgrade yt-dlp',
    'nix': 'nix-env -u yt-dlp   # or update via your nix profile',
    'snap': 'sudo snap refresh yt-dlp',
    'flatpak': 'flatpak update',
    'scoop': 'scoop update yt-dlp',
    'winget': 'winget upgrade yt-dlp',
    'npm': 'npm update -g yt-dlp',
    'system-managed-python': (
        'Your Python is system-managed (PEP 668). '
        'Install yt-dlp via your OS package manager, or use pipx: pipx install yt-dlp'
    ),
    'shim-interpreter': (
        'yt-dlp is installed via a shim manager (pyenv/asdf/mise). '
        'Use the underlying tool to upgrade.'
    ),
    'cannot-verify-owning-python': (
        'Could not verify which Python owns yt-dlp. '
        'Please upgrade manually using pip in that environment.'
    ),
    'unknown': 'Consult your package manager to upgrade yt-dlp.',
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_path(p: str) -> str:
    """Return a path with backslashes replaced by forward slashes and casefolded.

    We casefold on all platforms because the well-known package-manager paths
    we match against (Cellar, Microsoft/WinGet, ProgramData/chocolatey, etc.)
    use mixed case on disk, while our pattern constants are lowercase. No
    realistic Unix system has two manager paths that differ only in case.
    """
    if p is None:
        return ''
    return p.replace('\\', '/').casefold()


def _login_shell_discover(target: str) -> Optional[str]:
    """Discover the absolute path of `target` by invoking the user's login shell.

    Used as a fallback on macOS frozen .app launches where the inherited PATH
    excludes Homebrew, pipx, etc.
    """
    if pwd is None:
        return None

    shell = os.environ.get('SHELL')
    if not shell:
        try:
            shell = pwd.getpwuid(os.getuid()).pw_shell
        except (KeyError, OSError):
            shell = None

    if not shell or shell not in _SHELL_ALLOWLIST:
        shell = _FALLBACK_SHELL

    try:
        result = subprocess.run(
            [shell, '-l', '-c', f'command -v {target}'],
            capture_output=True,
            text=True,
            timeout=DISCOVERY_TIMEOUT,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None

    if result.returncode != 0:
        return None
    out = result.stdout.strip()
    return out or None


def _frozen_app_on_macos() -> bool:
    return sys.platform == 'darwin' and bool(getattr(sys, 'frozen', False))


def find_ytdlp_binary() -> Optional[str]:
    """Resolve the absolute realpath of the yt-dlp binary, or None if not found.

    On a macOS frozen .app, falls back to discovering via the user's login shell
    when the bundled PATH does not include the binary.
    """
    p = shutil.which('yt-dlp')
    if p is None and _frozen_app_on_macos():
        p = _login_shell_discover('yt-dlp')
    if p is None:
        return None
    try:
        return os.path.realpath(p)
    except OSError:
        return p


def find_package_manager_binary(name: str) -> Optional[str]:
    """Discover the absolute path of brew/pipx/choco using the same fallback chain."""
    p = shutil.which(name)
    if p is None and _frozen_app_on_macos():
        p = _login_shell_discover(name)
    if p is None:
        return None
    try:
        return os.path.realpath(p)
    except OSError:
        return p


# ---------------------------------------------------------------------------
# Install-method classification
# ---------------------------------------------------------------------------

# Magic bytes for real interpreters; everything else is treated as a shim/script.
_REAL_INTERPRETER_MAGICS = (
    b'\x7fELF',            # ELF (Linux, *BSD)
    b'\xfe\xed\xfa\xce',   # Mach-O 32-bit BE
    b'\xce\xfa\xed\xfe',   # Mach-O 32-bit LE
    b'\xfe\xed\xfa\xcf',   # Mach-O 64-bit BE
    b'\xcf\xfa\xed\xfe',   # Mach-O 64-bit LE
    b'\xca\xfe\xba\xbe',   # Mach-O Universal (fat) BE
    b'\xca\xfe\xba\xbf',   # Mach-O Universal 64
    b'MZ',                 # Windows PE
)


def _is_real_interpreter(magic: bytes) -> bool:
    return any(magic.startswith(m) for m in _REAL_INTERPRETER_MAGICS)


def _read_shebang(binary_path: str) -> Optional[str]:
    """Return the interpreter named on the first line's shebang, or None."""
    try:
        with open(binary_path, 'rb') as f:
            first = f.readline()
    except (OSError, ValueError):
        return None
    if not first.startswith(b'#!'):
        return None
    try:
        line = first[2:].decode('utf-8', errors='replace').strip()
    except Exception:
        return None
    if not line:
        return None
    parts = line.split()
    # Handle "/usr/bin/env python3" → look up "python3"
    if parts[0].endswith('/env') and len(parts) > 1:
        return shutil.which(parts[1])
    return parts[0]


def _extract_python_hint_from_venv(binary_path: str) -> Optional[str]:
    """If the binary lives in a venv's bin/Scripts dir, return the sibling python."""
    parent = os.path.dirname(binary_path)
    base = os.path.basename(parent).lower()
    if base in ('bin', 'scripts'):
        for candidate in ('python3', 'python', 'python.exe'):
            cand = os.path.join(parent, candidate)
            if os.path.isfile(cand):
                return cand
    return None


def _site_packages_root(path: str) -> Optional[str]:
    """Walk up `path` until a `site-packages` directory is found; return that dir."""
    cur = os.path.dirname(path) if os.path.isfile(path) else path
    seen = set()
    while cur and cur not in seen:
        seen.add(cur)
        base = os.path.basename(cur).lower()
        if base == 'site-packages':
            return cur
        cur = os.path.dirname(cur)
        if cur in ('/', '') or (sys.platform == 'win32' and re.match(r'^[a-zA-Z]:[/\\]?$', cur)):
            break
    return None


def _venv_root_from_binary(binary_path: str) -> Optional[str]:
    parent = os.path.dirname(binary_path)
    if os.path.basename(parent).lower() in ('bin', 'scripts'):
        return os.path.dirname(parent)
    return None


def _has_externally_managed_marker(prefix: str) -> bool:
    lib_dir = os.path.join(prefix, 'lib')
    if not os.path.isdir(lib_dir):
        return False
    try:
        for entry in os.listdir(lib_dir):
            if entry.startswith('python'):
                marker = os.path.join(lib_dir, entry, 'EXTERNALLY-MANAGED')
                if os.path.exists(marker):
                    return True
    except OSError:
        pass
    return False


def verify_owning_python(binary_path: str, hint: str) -> tuple[Optional[str], Optional[str]]:
    """Structurally verify that `hint` is the Python interpreter that owns the
    yt_dlp module rooted at the same install as `binary_path`.

    Returns (verified_python, unsupported_reason). On success, reason is None.
    """
    if not hint:
        return None, 'cannot-verify-owning-python'

    # Resolve symlinks; reject nonexistent.
    try:
        resolved = os.path.realpath(hint)
    except OSError:
        return None, 'cannot-verify-owning-python'
    if not os.path.exists(resolved):
        return None, 'cannot-verify-owning-python'

    # Shim detection via magic bytes (real interpreters are ELF/Mach-O/PE).
    try:
        with open(resolved, 'rb') as f:
            magic = f.read(256)
    except OSError:
        return None, 'cannot-verify-owning-python'
    if not _is_real_interpreter(magic):
        return None, 'shim-interpreter'

    # Probe the interpreter for yt_dlp ownership and venv shape.
    probe_code = (
        'import sys, yt_dlp; '
        'print(yt_dlp.__file__); '
        'print(sys.executable); '
        'print(sys.prefix); '
        'print(sys.base_prefix)'
    )
    try:
        result = subprocess.run(
            [resolved, '-c', probe_code],
            capture_output=True,
            text=True,
            timeout=PYTHON_VERIFY_TIMEOUT,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None, 'cannot-verify-owning-python'
    if result.returncode != 0:
        return None, 'cannot-verify-owning-python'

    lines = result.stdout.strip().split('\n')
    if len(lines) != 4:
        return None, 'cannot-verify-owning-python'
    yt_dlp_file, _sys_exec, sys_prefix, sys_base_prefix = lines

    # Site-packages match: prefer a direct site-packages root match.
    binary_sp = _site_packages_root(binary_path)
    module_sp = _site_packages_root(yt_dlp_file)
    if binary_sp and module_sp:
        if os.path.realpath(binary_sp) != os.path.realpath(module_sp):
            return None, 'cannot-verify-owning-python'
    else:
        # Fall back to venv-root match for the common case where the script
        # is `<venv>/bin/yt-dlp` (no `/site-packages/` in its path) but the
        # module lives under `<venv>/lib/python*/site-packages/yt_dlp/`.
        venv_root = _venv_root_from_binary(binary_path)
        if not venv_root or not module_sp:
            return None, 'cannot-verify-owning-python'
        # module_sp parent chain: site-packages → python3.X (or Lib) → venv_root
        parent = os.path.dirname(module_sp)
        if os.path.basename(parent).lower().startswith('python'):
            parent = os.path.dirname(parent)
        if os.path.basename(parent).lower() in ('lib', 'lib64'):
            parent = os.path.dirname(parent)
        if os.path.realpath(parent) != os.path.realpath(venv_root):
            return None, 'cannot-verify-owning-python'

    # System-managed Python rejection.
    if sys_prefix == sys_base_prefix:
        if _has_externally_managed_marker(sys_prefix):
            return None, 'system-managed-python'
        try:
            owner_dir = os.path.dirname(resolved)
            if not os.access(owner_dir, os.W_OK):
                return None, 'system-managed-python'
        except OSError:
            return None, 'system-managed-python'

    return resolved, None


def classify_install_method(
    binary_path: str,
) -> tuple[InstallMethod, Optional[str], Optional[str]]:
    """Classify the install method of a present yt-dlp binary.

    Returns (method, owning_python, unsupported_reason). NEVER returns 'missing'
    — the caller must handle binary_path is None before calling this function.

    Pattern tests run in this order, first match wins:
      1. pipx   (/pipx/)
      2. brew   (/Cellar/yt-dlp/, /opt/homebrew/, /usr/local/Cellar/)
      3. choco  (/chocolatey/)
      4. path-pattern unsupported (distro, shims, nix, snap, flatpak,
                                    scoop, winget, npm)
      5. filesystem-augmented unsupported (conda env via conda-meta sibling)
      6. pip    (verified via verify_owning_python)
      7. standalone (real executable in a user-writable location)
    """
    np = _normalize_path(binary_path)

    # 1. pipx
    if '/pipx/' in np:
        return 'pipx', None, None

    # 2. brew
    if (
        '/cellar/yt-dlp/' in np
        or np.startswith('/opt/homebrew/')
        or '/usr/local/cellar/' in np
    ):
        return 'brew', None, None

    # 3. choco
    if '/chocolatey/' in np:
        return 'choco', None, None

    # 4. path-pattern unsupported (distro, shims, sandboxes, scoop, winget, npm)
    for pattern, reason in _PATH_UNSUPPORTED_PATTERNS:
        if pattern in np:
            return 'unsupported', None, reason
    for prefix in _DISTRO_PREFIXES:
        if np.startswith(prefix):
            return 'unsupported', None, 'apt-or-dnf'

    # 5. filesystem-augmented unsupported (conda env)
    # Only classify as conda-managed if conda's package database actually
    # tracks yt-dlp (a `yt-dlp-*.json` file in conda-meta/). The bare presence
    # of a conda-meta/ directory is NOT sufficient: a very common setup is
    # `pip install yt-dlp` into the conda env's Python, which produces a
    # binary at <env>/bin/yt-dlp but no conda metadata. Those should fall
    # through to pip detection and be auto-upgraded via the owning Python's
    # pip.
    try:
        parent_dir = os.path.dirname(binary_path)
        env_dir = os.path.dirname(parent_dir)
        conda_meta = os.path.join(env_dir, 'conda-meta')
        if env_dir and os.path.isdir(conda_meta):
            try:
                entries = os.listdir(conda_meta)
            except OSError:
                entries = []
            conda_owns_ytdlp = any(
                e.startswith('yt-dlp-') and e.endswith('.json') for e in entries
            )
            if conda_owns_ytdlp:
                return 'unsupported', None, 'conda'
            # else: pip-installed into the conda env's Python — fall through.
    except OSError:
        pass

    # 6. pip with verification — only when there's a Python-looking hint.
    # A standalone binary's shebang (e.g. `#!/bin/sh`) is NOT a Python and
    # should fall through to step 7.
    python_hint: Optional[str] = _extract_python_hint_from_venv(binary_path)
    if python_hint is None:
        shebang = _read_shebang(binary_path)
        if shebang and 'python' in os.path.basename(shebang).lower():
            python_hint = shebang
    if python_hint:
        verified, reason = verify_owning_python(binary_path, python_hint)
        if verified:
            return 'pip', verified, None
        return 'unsupported', None, reason

    # 7. standalone (real executable in a user-writable location)
    try:
        if os.path.isfile(binary_path) and os.access(binary_path, os.X_OK):
            return 'standalone', None, None
    except OSError:
        pass

    return 'unsupported', None, 'unknown'


# ---------------------------------------------------------------------------
# Version queries
# ---------------------------------------------------------------------------

_VERSION_RE = re.compile(r'^v?(\d+(?:\.\d+)*)\s*$')


def query_installed_version(binary_path: str) -> tuple[Optional[str], Optional[str]]:
    """Return (version, error_reason). One is always None."""
    try:
        result = subprocess.run(
            [binary_path, '--version'],
            capture_output=True,
            text=True,
            timeout=INSTALLED_VERSION_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return None, 'timeout'
    except OSError as e:
        return None, f'oserror:{e.errno}'

    if result.returncode != 0:
        return None, f'exit_{result.returncode}'

    version = result.stdout.strip().splitlines()[0].strip() if result.stdout else ''
    if not version or not _VERSION_RE.match(version):
        return None, 'parse_error'
    return version, None


def query_latest_version(
    timeout: float = PYPI_TIMEOUT,
) -> tuple[Optional[str], Optional[str]]:
    """Return (latest_version, error_reason). One is always None."""
    req = urllib.request.Request(
        PYPI_URL,
        headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        return None, f'http_{e.code}'
    except urllib.error.URLError as e:
        return None, f'url_error:{e.reason}'
    except (TimeoutError, OSError) as e:
        return None, f'network:{e}'

    try:
        payload = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, 'parse_error'

    try:
        version = payload['info']['version']
    except (KeyError, TypeError):
        return None, 'parse_error'
    if not isinstance(version, str) or not version.strip():
        return None, 'parse_error'
    return version.strip(), None


def _parse_version(v: Optional[str]) -> Optional[tuple[int, ...]]:
    if not v:
        return None
    s = v.strip()
    if s.lower().startswith('v'):
        s = s[1:]
    parts = s.split('.')
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


def compare_versions(installed: Optional[str], latest: Optional[str]) -> Freshness:
    a = _parse_version(installed)
    b = _parse_version(latest)
    if a is None or b is None:
        return 'unknown'
    pad = max(len(a), len(b))
    a_pad = a + (0,) * (pad - len(a))
    b_pad = b + (0,) * (pad - len(b))
    if a_pad >= b_pad:
        return 'current'
    return 'outdated'


def format_check_error(
    installed_err: Optional[str], latest_err: Optional[str]
) -> Optional[str]:
    if installed_err and latest_err:
        return f'installed: {installed_err}; latest: {latest_err}'
    if installed_err:
        return f'installed: {installed_err}'
    if latest_err:
        return f'latest: {latest_err}'
    return None


# ---------------------------------------------------------------------------
# Upgrade command resolution
# ---------------------------------------------------------------------------

def _auto_command_for_unsupported(reason: Optional[str]) -> Optional[list[str]]:
    """Return an argv list for the unsupported-reason if we can attempt an
    auto-upgrade without prompting for sudo / modifying immutable stores.

    Some managers (apt, dnf, snap, nix) genuinely cannot be auto-upgraded
    from an interactive-less subprocess. Those return None and the worker
    falls back to printing the manual command.
    """
    if reason == 'conda':
        # -y skips the confirmation prompt; conda-forge has the freshest builds.
        conda = find_package_manager_binary('conda') or find_package_manager_binary('mamba')
        if conda:
            return [conda, 'update', '-y', '-c', 'conda-forge', 'yt-dlp']
        return None
    if reason == 'pyenv-shim':
        pyenv = find_package_manager_binary('pyenv')
        if pyenv:
            return [pyenv, 'exec', 'pip', 'install', '--upgrade', 'yt-dlp']
        return None
    if reason == 'asdf-shim':
        asdf = find_package_manager_binary('asdf')
        if asdf:
            return [asdf, 'exec', 'pip', 'install', '--upgrade', 'yt-dlp']
        return None
    if reason == 'mise-shim':
        mise = find_package_manager_binary('mise')
        if mise:
            return [mise, 'exec', '--', 'pip', 'install', '--upgrade', 'yt-dlp']
        return None
    if reason == 'scoop':
        scoop = find_package_manager_binary('scoop')
        if scoop:
            return [scoop, 'update', 'yt-dlp']
        return None
    if reason == 'winget':
        winget = find_package_manager_binary('winget')
        if winget:
            return [winget, 'upgrade', 'yt-dlp', '--silent', '--accept-source-agreements']
        return None
    if reason == 'npm':
        npm = find_package_manager_binary('npm')
        if npm:
            return [npm, 'update', '-g', 'yt-dlp']
        return None
    if reason == 'flatpak':
        flatpak = find_package_manager_binary('flatpak')
        if flatpak:
            return [flatpak, 'update', '-y', 'yt-dlp']
        return None
    # apt-or-dnf, snap, nix, unknown — auto-upgrade not feasible without sudo
    # or against an immutable store. Caller falls back to manual command.
    return None


def build_upgrade_command(status: YtDlpStatus) -> Optional[list[str]]:
    """Return the argv list for an auto-upgrade, or None when no safe command exists.

    All argv elements use absolute paths for package-manager binaries to avoid
    PATH ambiguity (relevant for frozen .app launches on macOS).
    """
    m = status.install_method
    if m == 'brew':
        brew = find_package_manager_binary('brew')
        if not brew:
            return None
        return [brew, 'upgrade', 'yt-dlp']
    if m == 'pipx':
        pipx_path = find_package_manager_binary('pipx')
        if not pipx_path:
            return None
        return [pipx_path, 'upgrade', 'yt-dlp']
    if m == 'choco':
        choco = find_package_manager_binary('choco')
        if not choco:
            return None
        return [choco, 'upgrade', 'yt-dlp', '-y']
    if m == 'pip':
        if not status.owning_python:
            return None
        return [status.owning_python, '-m', 'pip', 'install', '-U', 'yt-dlp']
    if m == 'standalone':
        if not status.binary_path:
            return None
        return [status.binary_path, '-U']
    if m == 'unsupported':
        # Best-effort auto-upgrade per detected manager (no-sudo managers only).
        return _auto_command_for_unsupported(status.unsupported_reason)
    return None


def build_manual_upgrade_instructions(status: YtDlpStatus) -> str:
    reason = status.unsupported_reason or 'unknown'
    return MANUAL_COMMANDS.get(reason, MANUAL_COMMANDS['unknown'])


# ---------------------------------------------------------------------------
# Worker thread
# ---------------------------------------------------------------------------

UpdaterMode = Literal['check_only', 'check_and_upgrade']


class YtDlpUpdaterThread(threading.Thread):
    """Background worker for yt-dlp version checks and upgrades.

    Communicates with the GUI exclusively via the shared message_queue using
    these message types:
      - 'ytdlp_status'           — one summary envelope per run
      - 'ytdlp_update_complete'  — fired only in 'check_and_upgrade' mode
      - 'log'                    — info/warning/error lines

    NEVER emits 'error', 'status', 'progress', 'video_progress', or 'complete'
    — those are reserved for ProcessorThread and trigger destructive UI flows.
    """

    def __init__(self, message_queue: queue.Queue, mode: UpdaterMode) -> None:
        super().__init__()
        self.message_queue = message_queue
        self.mode = mode
        self.daemon = True

    def _enqueue_log(self, level: str, message: str) -> None:
        self.message_queue.put({'type': 'log', 'level': level, 'message': message})

    def _enqueue_status(self, status: YtDlpStatus) -> None:
        msg = {'type': 'ytdlp_status'}
        msg.update(asdict(status))
        self.message_queue.put(msg)

    def _enqueue_update_complete(
        self,
        success: bool,
        exit_code: int,
        new_version: Optional[str],
        latest_version: Optional[str],
        reverified_freshness: Freshness,
    ) -> None:
        self.message_queue.put({
            'type': 'ytdlp_update_complete',
            'success': success,
            'exit_code': exit_code,
            'new_version': new_version,
            'latest_version': latest_version,
            'reverified_freshness': reverified_freshness,
        })

    def run(self) -> None:
        try:
            self._run_inner()
        except Exception as e:  # noqa: BLE001 — final safety net
            self._enqueue_log('error', f'yt-dlp updater error: {e}')
            if self.mode == 'check_and_upgrade':
                self._enqueue_update_complete(
                    success=False,
                    exit_code=-1,
                    new_version=None,
                    latest_version=None,
                    reverified_freshness='unknown',
                )
            else:
                self._enqueue_status(YtDlpStatus(
                    installed_version=None,
                    latest_version=None,
                    install_method='missing',
                    freshness='unknown',
                    binary_path=None,
                    owning_python=None,
                    check_error=f'updater_error: {e}',
                    unsupported_reason=None,
                    manual_command=None,
                ))

    # ------------------------------------------------------------------
    # Internal pipeline
    # ------------------------------------------------------------------

    def _run_inner(self) -> None:
        binary_path = find_ytdlp_binary()

        if binary_path is None:
            self._handle_missing()
            return

        method, owning_python, unsupported_reason = classify_install_method(binary_path)

        installed, installed_err = query_installed_version(binary_path)
        latest, latest_err = query_latest_version()
        freshness = compare_versions(installed, latest)
        check_error = format_check_error(installed_err, latest_err)

        manual_command: Optional[str] = None
        if method == 'unsupported':
            manual_command = MANUAL_COMMANDS.get(
                unsupported_reason or 'unknown', MANUAL_COMMANDS['unknown']
            )

        status = YtDlpStatus(
            installed_version=installed,
            latest_version=latest,
            install_method=method,
            freshness=freshness,
            binary_path=binary_path,
            owning_python=owning_python if method == 'pip' else None,
            check_error=check_error,
            unsupported_reason=unsupported_reason,
            manual_command=manual_command,
        )
        self._enqueue_status(status)

        if check_error:
            self._enqueue_log('info', f'yt-dlp version check: {check_error}')

        if self.mode == 'check_only':
            return

        self._handle_upgrade(status)

    def _handle_missing(self) -> None:
        status = YtDlpStatus(
            installed_version=None,
            latest_version=None,
            install_method='missing',
            freshness='missing',
            binary_path=None,
            owning_python=None,
            check_error=None,
            unsupported_reason=None,
            manual_command=None,
        )
        self._enqueue_status(status)
        if self.mode == 'check_and_upgrade':
            self._enqueue_log('info', 'yt-dlp is not installed; nothing to upgrade')
            self._enqueue_update_complete(
                success=False,
                exit_code=-3,
                new_version=None,
                latest_version=None,
                reverified_freshness='missing',
            )

    def _handle_upgrade(self, status: YtDlpStatus) -> None:
        # The mode MUST emit exactly one ytdlp_update_complete on every exit path
        # so the GUI clears _ytdlp_update_in_progress and re-enables the button.

        if status.freshness == 'current':
            self._enqueue_log(
                'info', f'yt-dlp is already up to date (latest: {status.latest_version})'
            )
            self._enqueue_update_complete(
                success=True,
                exit_code=0,
                new_version=status.installed_version,
                latest_version=status.latest_version,
                reverified_freshness='current',
            )
            return

        if status.freshness in ('unknown', 'missing'):
            self._enqueue_log(
                'info',
                'Cannot determine yt-dlp freshness; skipping upgrade.'
                f' (check_error={status.check_error})',
            )
            self._enqueue_update_complete(
                success=False,
                exit_code=-3,
                new_version=status.installed_version,
                latest_version=status.latest_version,
                reverified_freshness=status.freshness if status.freshness != 'missing' else 'unknown',
            )
            return

        # freshness == 'outdated'
        argv = build_upgrade_command(status)
        if argv is None:
            manual = build_manual_upgrade_instructions(status)
            self._enqueue_log(
                'info',
                f'No automatic upgrade available for install method "{status.install_method}". '
                f'Run: {manual}',
            )
            self._enqueue_update_complete(
                success=False,
                exit_code=-2,
                new_version=status.installed_version,
                latest_version=status.latest_version,
                reverified_freshness='outdated',
            )
            return

        # Run the upgrade subprocess.
        self._enqueue_log('info', f'Running upgrade: {" ".join(argv)}')
        exit_code = self._run_upgrade_subprocess(argv)

        # Re-verify against the same latest_version cached in `status`.
        new_binary = find_ytdlp_binary()
        if new_binary:
            new_version, _ = query_installed_version(new_binary)
        else:
            new_version = None
        reverified = compare_versions(new_version, status.latest_version)

        if exit_code == 0 and reverified == 'outdated':
            self._enqueue_log(
                'warning',
                f'Package manager reported success but installed version '
                f'({new_version}) is still older than latest '
                f'({status.latest_version}) — the package manager\'s repo '
                'may lag the upstream release',
            )
        elif exit_code == 0 and reverified == 'current':
            self._enqueue_log('info', f'yt-dlp updated to {new_version}')
        elif exit_code == 0:
            self._enqueue_log(
                'info',
                f'yt-dlp upgrade completed but re-verification was inconclusive '
                f'(new={new_version}, latest={status.latest_version})',
            )
        else:
            self._enqueue_log('error', f'yt-dlp update failed (exit code {exit_code})')

        self._enqueue_update_complete(
            success=(exit_code == 0),
            exit_code=exit_code,
            new_version=new_version,
            latest_version=status.latest_version,
            reverified_freshness=reverified,
        )

    def _run_upgrade_subprocess(self, argv: list[str]) -> int:
        try:
            proc = subprocess.Popen(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace',
            )
        except OSError as e:
            self._enqueue_log('error', f'Failed to start upgrade subprocess: {e}')
            return -1

        try:
            assert proc.stdout is not None
            for raw_line in proc.stdout:
                line = raw_line.rstrip('\r\n')
                if not line:
                    continue
                if line.startswith('ERROR:'):
                    level = 'error'
                elif line.startswith('WARNING:'):
                    level = 'warning'
                else:
                    level = 'info'
                self._enqueue_log(level, line)
            proc.wait()
        except Exception as e:  # noqa: BLE001
            self._enqueue_log('error', f'Error reading upgrade output: {e}')
            try:
                proc.kill()
            except OSError:
                pass
            return proc.returncode if proc.returncode is not None else -1

        return proc.returncode
