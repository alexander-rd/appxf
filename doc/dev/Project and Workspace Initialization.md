<!--Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)-->
<!--SPDX-License-Identifier: 0BSD-->
# Project and Workspace Initialization

## Ubuntu installations
(Collected, needs some refinement (one line)):
```bash
sudo apt-get install tox
sudo apt install python3.12-venv
sudo apt-get install flake8
sudo apt install gettext
```
## VENV
install pyenv and make python versions available: https://help.clouding.io/hc/en-us/articles/13555555842588-How-to-install-different-versions-of-Python-on-Ubuntu (Needs refinements/updates: exact lines on which versions to install; actually using pyenv)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e . -r requirements.txt -r requirements_test.txt
```
## Check Setup
Run commands to verify setup, each line separately.
```bash
pytest -rA
tox -e py312
flake8 --count src
python manual_test.py
python tests/gui/manual_whatever.py
python tests_features/gui/full_application/user_s0.py
```
The last three steps are for manual test case execution which can have their own issues.
# Obsidian Documentation
* The plugins are not checked in, only the configuration - you ***may*** need to install them manually (not confirmed)
* The plantuml plugin is configured to use a local jar file. You need to place the file into `.obsidian/plugins/obsidian-plantuml`
## Journal
### 15.06.2025
Problems with pip after changing from Ubuntu 22.04 to 24.04 (pip needs venv or packages must be installed via apt-get). This topic has two aspects:
 * venv is now mandatory when developing python
 * I did not yet resolve preparing for multiple python versions. 3.10 was not available via apt-get and I stopped digging deeper into pyenv.
Via apt-get: https://askubuntu.com/questions/682869/how-do-i-install-a-different-python-version-using-apt-get
Via pyenv: https://help.clouding.io/hc/en-us/articles/13555555842588-How-to-install-different-versions-of-Python-on-Ubuntu
