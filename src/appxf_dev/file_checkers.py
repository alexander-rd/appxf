# Copyright 2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import subprocess
import sys

# Expected copyright phrase has three parts:
#  * "Copyright "
#  * a single year, year range or a list of years or year ranges
#  * author or contributor reference
# Copyright lines are NOT expected to break into the next line(s). The years
# part is not checked.
COPYRIGHT_AUTHOR = 'the contributors of APPXF (github.com/alexander-rd/appxf)'

# License phrases are fixed strings and no alterations are expected. With
# SPDX-License-Identifier, only a single line is expected.
LICENSES = {
    '.py': 'SPDX-License-Identifier: Apache-2.0',
    '.sh': 'SPDX-License-Identifier: 0BSD',
}


def get_git_files() -> list[Path]:
    ''' Get list of files maintained by git

    The git repository is identified by the main caller's execution path.
    '''

    # identify root of git repository:
    root_result = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        cwd=Path.cwd(),
        check=True,
        capture_output=True,
        text=True,
    )
    repo_root = Path(root_result.stdout.strip())
    # get git tracked files separated by '\0' in one string (-z option):
    files_result = subprocess.run(
        ['git', 'ls-files', '-z'],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    return [repo_root / relative_file
            for relative_file in files_result.stdout.split('\0')
            if relative_file]

def verify_file_header(file: Path) -> bool:
    ''' Verify required information in file headers

    Expected are copyright and license information. Note some file types
    include this information on other places.
    '''
    has_copyright = False
    has_license = False

    if file.suffix in ['.py', '.sh']:
        # Expected are copyright lines followed by SPDX license identifyer
        # (Apache). There may be more copyright lines - only one must contain
        # the expected author/contributor text.
        with file.open(encoding='utf-8') as fh:
            while True:
                line = fh.readline().rstrip('\n')
                # resolve comment line:
                if not line.startswith('#'):
                    break
                line = line.lstrip('#').strip()
                if line.lower().startswith('copyright'):
                    if COPYRIGHT_AUTHOR in line:
                        has_copyright = True
                if line.startswith(LICENSES[file.suffix]):
                    has_license = True
    else:
        print(f'{file}:\n  Unsupported file type for header verification')
        return False

    if not has_copyright or not has_license:
        print(f'{file}:')
        if not has_copyright:
            print(f'  Missing or invalid copyright')
        if not has_license:
            print(f'  Missing SPDX license identifier: {LICENSES[".py"].split(": ")[1]}')
        return False
    return True

def verify_git_files() -> bool:
    ''' Verify that all git files are .py files '''
    file_list = get_git_files()
    verified = True
    for file in file_list:
        # skip directories
        if file.is_dir():
            continue

        if not verify_file_header(file):
            # verify_file() prints details while the loop shall continue to
            # report all findings.
            verified = False
    return verified


def main() -> int:
    is_verified = verify_git_files()
    return 0 if is_verified else 1


if __name__ == '__main__':
    raise SystemExit(main())
