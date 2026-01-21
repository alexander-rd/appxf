* Demo-Application
	* System localization
	* Enforced localization
* Ensure documented:
	* python -m pygettext -d kiss_cf -o locale/kiss_cf.pot src/kiss_cf/gui/registration_user.py
	* msgfmt locale/de/LC_MESSAGES/kiss_cf.po -o locale/de/LC_MESSAGES/kiss_cf.mo
	* sudo apt update && sudo apt install -y gettext
	* msgfmt --check --statistics
	* General translation idea (for DEV)
	* Stub on public translation feature
