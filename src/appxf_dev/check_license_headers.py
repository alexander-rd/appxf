# Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
import subprocess
from fnmatch import fnmatch
from pathlib import Path

# Expected copyright phrase has three parts:
#  * "Copyright "
#  * a single year, year range or a list of years or year ranges
#  * author or contributor reference
# Copyright lines are NOT expected to break into the next line(s). The years
# part is not checked.
COPYRIGHT_AUTHOR = "the contributors of APPXF (github.com/alexander-nbg/appxf)"

# License phrases are fixed strings and no alterations are expected. With
# SPDX-License-Identifier, only a single line is expected.
LICENSES = {
    ".py": "SPDX-License-Identifier: Apache-2.0",
    ".po": "SPDX-License-Identifier: Apache-2.0",
    ".pot": "SPDX-License-Identifier: Apache-2.0",
    ".feature": "SPDX-License-Identifier: Apache-2.0",
    ".toml": "SPDX-License-Identifier: 0BSD",
    ".sh": "SPDX-License-Identifier: 0BSD",
    ".yml": "SPDX-License-Identifier: 0BSD",
    ".yaml": "SPDX-License-Identifier: 0BSD",
    ".md": "SPDX-License-Identifier: 0BSD",
    ".puml": "SPDX-License-Identifier: 0BSD",
}

EXCLUSION_FILE = "LICENSE"
EXCLUSION_START_MARKER = "FILES WITHOUT LICENSE TAGS"


def get_git_repo_root() -> Path:
    """Identify root path of the current git repository"""

    root_result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=Path.cwd(),
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(root_result.stdout.strip())


def get_git_files() -> list[Path]:
    """Get list of files maintained by git

    The git repository is identified by the main caller's execution path.
    """

    # identify root of git repository:
    repo_root = get_git_repo_root()
    # get git tracked files separated by '\0' in one string (-z option):
    files_result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    return [
        relative_file
        for relative_file in files_result.stdout.split("\0")
        if relative_file
    ]


def get_exclusion_patterns() -> list[str]:
    """Read exclusion patterns"""
    repo_root = get_git_repo_root()
    exclusion_file = repo_root / EXCLUSION_FILE
    found_marker = False
    pattern_list = []
    with exclusion_file.open(encoding="utf-8") as fh:
        for line in fh:
            if not found_marker and EXCLUSION_START_MARKER in line:
                found_marker = True
                continue

            line = line.strip()
            if line.startswith("* "):
                pattern = line[2:].strip()
                pattern_list.append(pattern)
    return pattern_list


def is_excluded_file(file: str, repo_root: Path, patterns: list[str]) -> bool:
    """Check if file matches an exclusion pattern"""
    return any(fnmatch(file, pattern) for pattern in patterns)


def verify_file_header(file: Path) -> bool:
    """Verify required information in file headers

    Expected are copyright and license information. Note some file types
    include this information on other places.
    """
    has_copyright = False
    has_license = False

    if file.suffix in [
        ".py",
        ".pot",
        ".po",
        ".feature",
        ".toml",
        ".sh",
        ".yml",
        ".yaml",
    ]:
        # Expected are copyright lines followed by SPDX license identifyer
        # (Apache). There may be more copyright lines - only one must contain
        # the expected author/contributor text.
        with file.open(encoding="utf-8") as fh:
            while True:
                line = fh.readline().rstrip("\n")
                # resolve comment line:
                if not line.startswith("#"):
                    break
                line = line.lstrip("#").strip()
                if line.lower().startswith("copyright") and COPYRIGHT_AUTHOR in line:
                    has_copyright = True
                if line.startswith(LICENSES[file.suffix]):
                    has_license = True
    elif file.suffix in [".md"]:
        with file.open(encoding="utf-8") as fh:
            while True:
                line = fh.readline().rstrip("\n").strip()
                # resolve comment line:
                if not line.startswith("<!--"):
                    break
                line = line.removeprefix("<!--").removesuffix("-->").strip()
                if line.lower().startswith("copyright") and COPYRIGHT_AUTHOR in line:
                    has_copyright = True
                if line.startswith(LICENSES[file.suffix]):
                    has_license = True
    elif file.suffix in [".puml"]:
        with file.open(encoding="utf-8") as fh:
            while True:
                line = fh.readline().rstrip("\n").strip()
                # resolve comment line:
                if not line.startswith("'"):
                    break
                line = line.removeprefix("'").strip()
                if line.lower().startswith("copyright") and COPYRIGHT_AUTHOR in line:
                    has_copyright = True
                if line.startswith(LICENSES[file.suffix]):
                    has_license = True
    else:
        print(f"{file}:\n  Unsupported file type for header verification")
        return False

    if not has_copyright or not has_license:
        print(f"{file}:")
        if not has_copyright:
            print("  Missing or invalid copyright")
        if not has_license:
            spdx_id = LICENSES[file.suffix].split(": ")[1]
            print(f"  Missing SPDX license identifier: {spdx_id}")
        return False
    return True


def verify_git_files() -> bool:
    """Verify that all git files are .py files"""
    file_list = get_git_files()
    repo_root = get_git_repo_root()
    exclusion_patterns = get_exclusion_patterns()

    not_verified_files = 0
    for file in file_list:
        absolute_file = repo_root / file
        # skip directories
        if absolute_file.is_dir():
            continue

        if is_excluded_file(file, repo_root, exclusion_patterns):
            continue

        if not verify_file_header(absolute_file):
            # verify_file() prints details while the loop shall continue to
            # report all findings.
            not_verified_files += 1

    if not_verified_files:
        print(f"{not_verified_files} file(s) failed copyright/license verification.")
        print(
            "Please add corresonding information. If not applicable, add "
            "files explicitly to the LICENSE text file."
        )
    else:
        print("Copyright/License information verified for all maintained files.")
    return not_verified_files == 0


def main() -> int:
    is_verified = verify_git_files()
    return 0 if is_verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
