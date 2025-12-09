## 01.12.2025 Re-Initializing VENV after moving the local folders
sudo apt install python3.12-venv
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e . -r requirements.txt -r requirements_test.txt

Checking if things work:
> pytest -rA
> tox -e py312

Note: python versions must be installed in ubuntu to have them available.

## Some hints when initializing the development environment
 * Install pyenv and make python versions available: https://help.clouding.io/hc/en-us/articles/13555555842588-How-to-install-different-versions-of-Python-on-Ubuntu
 * sudo apt-get install tox

# Journal
## 15.06.2025 
Problems with pip after changing from Ubuntu 22.04 to 24.04 (pip needs venv or packages must be installed via apt-get). This topic has two aspects:
 * I have to work with venv when developing python
 * Since I need to adapt, I want to be ready for mutiple python versions (like
   3.10 and 3.12 in parallel)

Via apt-get: https://askubuntu.com/questions/682869/how-do-i-install-a-different-python-version-using-apt-get
Via pyenv: https://help.clouding.io/hc/en-us/articles/13555555842588-How-to-install-different-versions-of-Python-on-Ubuntu

Pyenv seems to be the de-facto standard.

