#!/usr/bin/env python3
"""
Build Script for PowerHour Generator

This script automates the build process for creating distributable
packages and executables for the PowerHour Generator application.

Usage:
    python build.py [options]
    
Options:
    --platform all|windows|macos|linux
    --type exe|wheel|source
    --clean
    --test
"""

import sys
import os
import re
import shutil
import subprocess
import platform
from pathlib import Path
import argparse
import zipfile
import tarfile


def _read_version(root_dir):
    """Parse __version__ from powerhour/__init__.py (canonical version source)."""
    init_file = root_dir / 'powerhour' / '__init__.py'
    match = re.search(
        r"""^__version__\s*=\s*['"]([^'"]+)['"]""",
        init_file.read_text(encoding='utf-8'),
        re.MULTILINE,
    )
    if not match:
        raise RuntimeError(f"Could not find __version__ in {init_file}")
    return match.group(1)


class Builder:
    """Handles the build process for PowerHour Generator"""

    def __init__(self):
        # scripts/build.py lives under scripts/, so root is its parent's parent.
        self.root_dir = Path(__file__).parent.parent.absolute()
        self.dist_dir = self.root_dir / 'dist'
        self.build_dir = self.root_dir / 'build'
        self.release_dir = self.root_dir / 'releases'
        self.platform = platform.system().lower()
        self.version = _read_version(self.root_dir)
        
    def clean(self):
        """Clean build artifacts"""
        print("🧹 Cleaning build artifacts...")
        
        # Remove build directories
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"   Removed {dir_path}")
        
        # Remove Python cache files
        for pattern in ['*.pyc', '__pycache__', '*.egg-info', '.pytest_cache']:
            for path in self.root_dir.rglob(pattern):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
        
        print("✅ Clean complete")
    
    def install_dependencies(self):
        """Install required dependencies"""
        print("📦 Installing dependencies...")
        
        # Install regular requirements
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        
        # Install dev requirements for building
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements-dev.txt'], check=True)
        
        print("✅ Dependencies installed")
    
    def build_executable(self, platform_name=None):
        """Build executable using PyInstaller"""
        platform_name = platform_name or self.platform
        
        print(f"🔨 Building executable for {platform_name}...")
        
        # Ensure PyInstaller is installed
        try:
            import PyInstaller
        except ImportError:
            print("Installing PyInstaller...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        
        # Run PyInstaller
        cmd = [sys.executable, '-m', 'PyInstaller', 'powerhour.spec', '--clean', '--noconfirm']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Build failed:\n{result.stderr}")
            return False
        
        print(f"✅ Executable built successfully in dist/PowerHourGenerator/")
        return True
    
    def build_wheel(self):
        """Build wheel distribution"""
        print("🎡 Building wheel distribution...")
        
        # Build wheel
        subprocess.run([sys.executable, 'setup.py', 'bdist_wheel'], check=True)
        
        print("✅ Wheel built successfully")
        return True
    
    def build_source(self):
        """Build source distribution"""
        print("📦 Building source distribution...")
        
        # Build source distribution
        subprocess.run([sys.executable, 'setup.py', 'sdist'], check=True)
        
        print("✅ Source distribution built successfully")
        return True
    
    def create_release_package(self, platform_name=None):
        """Create a release package with executable and documentation"""
        platform_name = platform_name or self.platform
        
        print(f"📦 Creating release package for {platform_name}...")
        
        # Create release directory
        self.release_dir.mkdir(exist_ok=True)
        
        # Define package name
        package_name = f"PowerHourGenerator-{self.version}-{platform_name}"
        package_dir = self.release_dir / package_name
        
        # Remove old package if exists
        if package_dir.exists():
            shutil.rmtree(package_dir)
        
        package_dir.mkdir()
        
        # Copy executable
        exe_source = self.dist_dir / 'PowerHourGenerator'
        if exe_source.exists():
            shutil.copytree(exe_source, package_dir / 'PowerHourGenerator')
        
        # Copy documentation. README and LICENSE live at the repo root; the rest live in docs/.
        root_docs = ['README.md', 'LICENSE']
        sub_docs = ['USER_GUIDE.md', 'DEVELOPING.md', 'CHANGELOG.md', 'RELEASE.md']

        docs_dir = package_dir / 'docs'
        docs_dir.mkdir()

        for doc in root_docs:
            doc_path = self.root_dir / doc
            if doc_path.exists():
                shutil.copy(doc_path, docs_dir)

        for doc in sub_docs:
            doc_path = self.root_dir / 'docs' / doc
            if doc_path.exists():
                shutil.copy(doc_path, docs_dir)
        
        # Create archive
        if platform_name == 'windows':
            # Create ZIP for Windows
            archive_name = f"{package_name}.zip"
            archive_path = self.release_dir / archive_name
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(package_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(self.release_dir)
                        zf.write(file_path, arcname)
            
            print(f"✅ Release package created: {archive_path}")
        
        else:
            # Create tar.gz for Unix-like systems
            archive_name = f"{package_name}.tar.gz"
            archive_path = self.release_dir / archive_name
            
            with tarfile.open(archive_path, 'w:gz') as tf:
                tf.add(package_dir, arcname=package_name)
            
            print(f"✅ Release package created: {archive_path}")
        
        # Clean up temporary directory
        shutil.rmtree(package_dir)
        
        return archive_path
    
    def run_tests(self):
        """Run test suite"""
        print("🧪 Running tests...")
        
        # Check if pytest is installed
        try:
            import pytest
        except ImportError:
            print("Installing pytest...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pytest'], check=True)
        
        # Run tests
        result = subprocess.run([sys.executable, '-m', 'pytest', 'tests/', '-v'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Tests failed:\n{result.stdout}")
            return False
        
        print("✅ All tests passed")
        return True
    
    def verify_installation(self):
        """Verify that the package can be installed"""
        print("🔍 Verifying installation...")
        
        # Create a temporary virtual environment
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_dir = Path(tmpdir) / 'venv'
            
            # Create virtual environment
            subprocess.run([sys.executable, '-m', 'venv', str(venv_dir)], check=True)
            
            # Get pip path in venv
            if platform.system() == 'Windows':
                pip_path = venv_dir / 'Scripts' / 'pip.exe'
            else:
                pip_path = venv_dir / 'bin' / 'pip'
            
            # Install the package
            subprocess.run([str(pip_path), 'install', '.'], cwd=self.root_dir, check=True)
            
            print("✅ Installation verification complete")
            return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Build PowerHour Generator')
    parser.add_argument('--platform', choices=['all', 'windows', 'macos', 'linux'],
                       default='current', help='Target platform')
    parser.add_argument('--type', choices=['exe', 'wheel', 'source', 'all'],
                       default='exe', help='Build type')
    parser.add_argument('--clean', action='store_true', help='Clean before building')
    parser.add_argument('--test', action='store_true', help='Run tests before building')
    parser.add_argument('--release', action='store_true', help='Create release package')
    
    args = parser.parse_args()
    
    builder = Builder()
    
    # Clean if requested
    if args.clean:
        builder.clean()
    
    # Install dependencies
    builder.install_dependencies()
    
    # Run tests if requested
    if args.test:
        if not builder.run_tests():
            print("❌ Build aborted due to test failures")
            return 1
    
    # Perform build
    success = True
    
    if args.type in ['exe', 'all']:
        if args.platform == 'all':
            # Note: Cross-platform builds require special setup
            print("⚠️  Cross-platform builds require platform-specific environments")
            print("   Building for current platform only...")
            success = builder.build_executable()
        else:
            platform_name = args.platform if args.platform != 'current' else None
            success = builder.build_executable(platform_name)
    
    if args.type in ['wheel', 'all']:
        success = success and builder.build_wheel()
    
    if args.type in ['source', 'all']:
        success = success and builder.build_source()
    
    # Create release package if requested
    if success and args.release:
        builder.create_release_package()
    
    if success:
        print("\n🎉 Build completed successfully!")
        print(f"   Output directory: {builder.dist_dir}")
    else:
        print("\n❌ Build failed!")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())