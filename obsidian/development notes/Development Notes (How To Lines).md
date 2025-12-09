### Install package after checkout
Execute from where setup.py is located:
pip install -e .
### install package in .venv
(to ensure Phylance in visual code finds the sources):
source .venv/bin/activate
.. then pip install \<whatever\>

**run tests via tox:**
tox

**run tests via pytest** (might require being in venv (see above)) 
pytest -rA
pytest -rA tests/test_\<specific\>.py 

**run manual tests** (the PYTHONPATH prepend is necessary because python would execute the script from it's path and an otherwise empty python evironment)
`PYTHONPATH=. python tests_features/user_registry/manual_registration_request.py`

### profiling
(look in /prof) pip install pytest-profiling pytest -rA --profile --profile-svg

### Allow browser to read HTML reports in OS like Ubuntu 24.10
python -m http.server

### Flake8 manual
flake8 --count src

# GIT
### Changes between working dir and last commit when current commit is in preparation
git diff --name-only HEAD~1

## Branching
git checkout -b <ticket-number>_short_title
git push -u origin <branch-name>
# (checkout branch)

# merging
git checkout main
git merge <branch-name>
git push
# cleanup branch
git branch -d <branch-name>
git push origin --delete <branch-name>

## Others
 * Reproduce: errors are not shown in the log file (like wrong database conrhyfig, likely
   also missing template file)

Mitarbeit:
 * Consider Status of Mitarbeitstag

OpenOlitor TODO:

 * % Verplanung bei Mitbarbeit-Übersicht
 * Notwendige Dateien als Teil des Builds (schnelleres Verteilen)
   + ODS template
   + passwörter

Working on Email Templates:
 * Checkin Naming changes for Property->Setting (GUI)
 ** Update manual GUI testing scripts
 ** Do not yet check in SettingSelect
 ** Update documentation of StorageDummy
 ** ?? Utilize StorageMock as Dummy (aka RamStorage or Buffer) ??
 * Show SettingSelect in GUI