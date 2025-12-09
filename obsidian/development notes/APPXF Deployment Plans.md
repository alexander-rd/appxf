 * Until 0.1.0, kiss_cf and SolawiApp will verify appxf BEFORE the release. They
   will use a current version from my checkout or from Github.
 * After 0.1.0, kiss_cf and SolawiApp shall be treated as normal appxf users.
   Changes shall be requested via ticket. kiss_cf and SolawiApp will need to
   wait for a release.

First stable parts:
 * security
 * logging
 * storage
 * properties
 * config
 * buffer

NOT ready:
 * application and gui
 * registry
 * mariadb / openolitor
 * sendmail

Helpful pages:
https://packaging.python.org/en/latest/tutorials/packaging-projects/
https://drivendata.co/blog/python-packaging-2023

pip install --upgrade build
python -m build
pip install --upgrade twine
python -m twine upload --repository-url https://upload.pypi.org/legacy/ -u __token__ -p pypi-XXX dist/*

git tag v0.0.1
git push origin --tags

# APPXF Releases
0.0.2:
* Write and re-decide licensing. After what happened with PySimpleGui, I
  have to reconsider the free license. Push my notes into a license MD file.
  Describe use cases.
* review the existing code and refine the TODO remarks.
* add a template for "others"
* review pyproject.toml. Add requirements like babel which can then be removed from kiss.
* kiss_cf and Solawi will need to find a way to use the new but not yet released version.

0.0.1: Initial release with logging and fileversions.

0.0.2: Allow to start multiple base loggers.

LATER:

1.0.0:
* Consider adding a ticket template for "my project", encouraging others
  to tell how they are using appxf. This may be important for the beginning of
  appxf.