<!--Copyright 2026 the contributors of APPXF (github.com/alexander-rd/appxf)-->
<!--SPDX-License-Identifier: 0BSD-->
Helpful pages:
https://py-pkgs.org/welcome
https://packaging.python.org/en/latest/tutorials/packaging-projects/
https://drivendata.co/blog/python-packaging-2023

pip install --upgrade build
python -m build
pip install --upgrade twine
python -m twine upload --repository-url https://upload.pypi.org/legacy/ -u __token__ -p pypi-XXX dist/*

