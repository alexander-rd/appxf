#!/usr/bin/env python3
# Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""
Cross-platform PyInstaller build script.

This script provides a unified way to build Python applications using PyInstaller
across different platforms (Linux, Windows, macOS). It handles virtual environment
creation, dependency installation, and packaging.
"""

import argparse
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

# Build directory paths (module-level constants)
BUILD_DIR = Path("./build")
ENV_PATH = BUILD_DIR / ".env"
DIST_PATH = BUILD_DIR / "dist"


def elapsed_time(start: float) -> str:
    """Return elapsed time in seconds with one decimal place."""
    return f"{time.time() - start:.1f}s"


class _StepLogger:
    """Context manager for logging build steps with timing."""

    def __init__(self, message: str):
        self.message = message
        self.start_time = None

    def __enter__(self):
        print(f"\n{'=' * 60}")
        print(self.message)
        print(f"{'-' * 60}")
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            print(f"{'-' * 60}")
            print(f"Done ({elapsed_time(self.start_time)}); {self.message}")
            print(f"{'=' * 60}")
        return False


def run_command(
    cmd: List[str],
    shell: bool = False,
    check: bool = True,
    verbose: bool = False,
    **kwargs,
) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    if verbose:
        print(f"Running: {' '.join(cmd)}")

    # Suppress output unless verbose or capture_output is set
    if not verbose and "capture_output" not in kwargs:
        result = subprocess.run(
            cmd,
            shell=shell,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            **kwargs,
        )
        # Only print if there's an error or warning
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result
    else:
        if verbose:
            return subprocess.run(cmd, shell=shell, check=check, **kwargs)
        else:
            return subprocess.run(cmd, shell=shell, check=check, **kwargs)


def create_venv(cleanup: bool = False, verbose: bool = False) -> None:
    """Create a virtual environment at ./build/.env"""
    # Remove existing environment if cleanup is requested
    if cleanup and ENV_PATH.exists():
        print(f"  Cleaning: Removing existing environment at {ENV_PATH}")
        shutil.rmtree(ENV_PATH)

    # Create parent directory
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Use system default Python
    if not ENV_PATH.exists():
        run_command(["python", "-m", "venv", str(ENV_PATH)], verbose=verbose)
        print(f"  Virtual environment created at {ENV_PATH}")
    else:
        print(f"  Virtual environment already exists at {ENV_PATH}")


def get_activation_script() -> str:
    """Get the activation script command for the virtual environment."""
    if platform.system() == "Windows":
        return str(ENV_PATH / "Scripts" / "activate.bat")
    else:
        return f"source {ENV_PATH / 'bin' / 'activate'}"


def run_in_venv(
    cmd: List[str], verbose: bool = False, **kwargs
) -> subprocess.CompletedProcess:
    """Run a command within the virtual environment."""
    # Use the full path to the venv executables (works on all platforms)
    if platform.system() == "Windows":
        venv_bin = ENV_PATH / "Scripts"
        exe_suffix = ".exe"
    else:
        venv_bin = ENV_PATH / "bin"
        exe_suffix = ""

    # Replace python/pip/pyinstaller with full venv path
    if cmd[0] in ["python", "pip", "pyinstaller"]:
        cmd[0] = str(venv_bin / f"{cmd[0]}{exe_suffix}")

    return run_command(cmd, verbose=verbose, **kwargs)


def install_requirements(
    requirements_files: List[Path], editable_packages: List[Path], verbose: bool = False
) -> None:
    """Install requirements in the virtual environment."""
    # Install requirements files
    for req_file in requirements_files:
        if req_file.exists():
            print(f"  Installing from {req_file}")
            run_in_venv(["pip", "install", "-r", str(req_file)], verbose=verbose)
        else:
            print(f"  Warning: Requirements file {req_file} not found, skipping")

    # Install editable packages
    for package in editable_packages:
        if package.exists():
            print(f"  Installing editable package from {package}")
            run_in_venv(["pip", "install", "-e", str(package)], verbose=verbose)
        else:
            print(f"  Warning: Editable package path {package} not found, skipping")

    # Install PyInstaller
    print("  Installing PyInstaller")
    run_in_venv(["pip", "install", "pyinstaller"], verbose=verbose)


def build(
    main_file: Path,
    debug_build: bool = False,
    hidden_imports: Optional[List[str]] = None,
    strip: bool = True,
    verbose: bool = False,
) -> None:
    """Build executable via PyInstaller"""
    # Base command
    cmd = [
        "python",
        "-m",
        "PyInstaller",
        str(main_file),
        "--onefile",
        "--clean",
    ]

    # Add hidden imports
    if hidden_imports:
        for imp in hidden_imports:
            cmd.extend(["--hidden-import", imp])

    # Add strip option (only for Linux/macOS)
    if strip and platform.system() != "Windows":
        cmd.append("--strip")

    # Add debug options
    if debug_build:
        cmd.extend(["--debug", "all"])
        cmd.extend(["--name", f"{main_file.stem}_debug"])

    # Set dist path
    cmd.extend(["--distpath", str(DIST_PATH)])

    run_in_venv(cmd, verbose=verbose)


def copy_additional_files(files: List[Path]) -> None:
    """Copy additional files to the dist directory."""
    DIST_PATH.mkdir(parents=True, exist_ok=True)

    for file_path in files:
        if file_path.exists():
            dest = DIST_PATH / file_path.name
            print(f"  Copying {file_path} -> {dest}")
            shutil.copy2(file_path, dest)
        else:
            print(f"  Warning: File {file_path} not found, skipping")


def save_build_info(verbose: bool = False) -> None:
    """Save Python version and package information."""
    DIST_PATH.mkdir(parents=True, exist_ok=True)
    info_file = DIST_PATH / "python_versions.txt"

    with open(info_file, "w") as f:
        # Get Python version
        result = run_in_venv(
            ["python", "--version"], capture_output=True, text=True, verbose=verbose
        )
        f.write(result.stdout)

        # Get pip freeze
        result = run_in_venv(
            ["pip", "freeze"], capture_output=True, text=True, verbose=verbose
        )
        f.write(result.stdout)

    print(f"  Build information saved to {info_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="APPXF PyInstaller build script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --main-file app.py
  %(prog)s -m app.py --additional-files data.csv config.ini
  %(prog)s -m app.py -a template.xlsx --clean --verbose
  %(prog)s -m app.py --hidden-imports babel.numbers --no-strip

Build outputs:
  - Virtual environment: ./build/.env
  - Distribution files: ./build/dist/
        """,
    )

    # Mandatory arguments
    parser.add_argument(
        "-m", "--main-file", required=True, type=Path, help="Main Python file to build"
    )

    # Optional arguments
    parser.add_argument(
        "-a",
        "--additional-files",
        type=Path,
        nargs="*",
        default=[],
        help="Additional files to copy to dist directory",
    )
    parser.add_argument(
        "-r",
        "--requirements",
        type=Path,
        nargs="*",
        default=[],
        help=(
            "Additional requirements files to install "
            "(default: requirements.txt, appxf/requirements.txt)"
        ),
    )
    parser.add_argument(
        "--editable-packages",
        type=Path,
        nargs="*",
        default=[],
        help="Paths to packages to install in editable mode (default: appxf)",
    )
    parser.add_argument(
        "--hidden-imports", nargs="*", default=[], help="Hidden imports for PyInstaller"
    )
    parser.add_argument(
        "--no-strip", action="store_true", help="Disable strip option for PyInstaller"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Also create a debug build"
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean build directory before building"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed command output"
    )

    args = parser.parse_args()

    # Convert to absolute paths
    main_file = args.main_file.resolve()

    # Set default requirements if none provided
    requirements_files = (
        args.requirements
        if args.requirements
        else [
            Path("requirements.txt"),
            Path("appxf/requirements.txt"),
        ]
    )

    # Set default editable packages if none provided
    editable_packages = (
        args.editable_packages
        if args.editable_packages
        else [
            Path("appxf"),
        ]
    )

    print(f"{'=' * 60}")
    print("PyInstaller Build Script")
    print(f"{'=' * 60}")
    print(f"Platform: {platform.system()}")
    print(f"Main file: {main_file}")
    print("Build directory: ./build/")
    print(f"Clean build: {args.clean}")
    print(f"Verbose: {args.verbose}")
    print(f"{'=' * 60}")

    # Validate main file exists
    if not main_file.exists():
        print(f"Error: Main file {main_file} not found!")
        sys.exit(1)

    start_total = time.time()

    try:
        # Clean build directory if requested
        if args.clean:
            if BUILD_DIR.exists():
                print(f"\nCleaning build directory: {BUILD_DIR}")
                shutil.rmtree(BUILD_DIR)

        # Create virtual environment
        with _StepLogger("Creating virtual environment"):
            create_venv(cleanup=args.clean, verbose=args.verbose)

        # Install requirements
        with _StepLogger("Installing requirements"):
            install_requirements(
                requirements_files, editable_packages, verbose=args.verbose
            )

        # Build with PyInstaller (release)
        with _StepLogger("Building release version with PyInstaller"):
            build(
                main_file,
                debug_build=False,
                hidden_imports=args.hidden_imports if args.hidden_imports else None,
                strip=not args.no_strip,
                verbose=args.verbose,
            )

        # Build debug version if requested
        if args.debug:
            with _StepLogger("Building debug version with PyInstaller"):
                build(
                    main_file,
                    debug_build=True,
                    hidden_imports=args.hidden_imports if args.hidden_imports else None,
                    strip=not args.no_strip,
                    verbose=args.verbose,
                )

        # Copy additional files
        if args.additional_files:
            with _StepLogger("Copying additional files to dist"):
                copy_additional_files(args.additional_files)

        # Save build info
        with _StepLogger("Saving build information"):
            save_build_info(verbose=args.verbose)

        print(f"\n{'=' * 60}")
        print(
            f"Build completed successfully! (Total time: {elapsed_time(start_total)})"
        )
        print(f"{'=' * 60}")

    except subprocess.CalledProcessError as e:
        print(f"\nError: Build failed with exit code {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
