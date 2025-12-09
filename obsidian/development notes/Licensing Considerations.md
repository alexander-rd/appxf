## Conclusions

  * Put license notice in all files to avoid ambiguitiy. See:
    https://www.gnu.org/licenses/gpl-faq.html#NoticeInSourceFile
  * Documentation should explain the license shortly and may reference the FAQ:
    https://www.gnu.org/licenses/gpl-faq.html

Collect license information:
  pip-licenses --from-classifier --with-urls --with-system --format=markdown

Choosing a license:
  https://docs.python-guide.org/writing/license/
Very good overview:
  https://www.gnu.org/licenses/license-list.html
An article with statistics from PyPi:
  https://snyk.io/de/blog/over-10-of-python-packages-on-pypi-are-distributed-without-any-license/

GPL release would force a GPL license if result is published:
  https://www.gnu.org/licenses/gpl-faq.html#IfLibraryIsGPL
If a GPL part is included, the package must have a GPL license (for the whole
thing to work). But the part may be released with additional license options. !! This implies
  https://www.gnu.org/licenses/gpl-faq.html#GPLModuleLicense
Generally, the PACKAGE does not include the other packages (under GPL) and can
choose the license freely but compatible with the GPL. Only a shipped runnable
will combine it. !! Beware the testing that may incorporate the GPL module !!



Is code that would produce a combined work considered "combined work"

## GPL versus LGPL

APPXL is not for proprietary applications. Commercial applications would use
other frameworks and setups. Only someone who want's to make a business from
APPXL would generate applciations and distribute them. This shall be allowed
such that LPGL would be the choice.

Helpful: https://www.gnu.org/licenses/why-not-lgpl.html

## LGPL versus more freely

In case APPXL is successful, I do NOT want someone to take over and hide it
proprietarily. Others clearly would have more manpower to improve this library.
Clear aim is that improvements shall remain free.

GPL: No later restricted usage. Once it is GPL, I cannot start distributing it
exclusively. See:
https://www.gnu.org/licenses/gpl-faq.html#CanDeveloperThirdParty

GPL: Disclaimer may be needed when adding linking/shipping combined code. See:
https://opensource.stackexchange.com/questions/9189/python-package-with-different-licenses-per-modules-some-with-gpl-is-a-global-g

PyInstaller: will imply GPL license. APPXF should add those remarks in the
documentation on how to prepare distributables. See:
https://velovix.github.io/post/lgpl-gpl-license-compliance-with-pyinstaller/

An include statement and calling functions of a GPL/LGPL library makes the new
code 'derived' work. See:
https://opensource.stackexchange.com/questions/13824/gnu-gpl-license-in-libraries-in-python-requirements

GPL or LGPL packages: PyQt (GPL3).. ..not many at all.

Article on why GPL fails. Bottom line is cloud servies are the larger problem
and GPL only forces making derivative work public but NOT behaving well (fixing
bugs). See: https://martin.kleppmann.com/2021/04/14/goodbye-gpl.html

A further note on tendencies: https://opensource.com/article/17/2/decline-gpl

Gernally, the GPL is a long text and hard to get right. It may block users from
actually using APPXF.

## License listing

Example scipy: https://github.com/scipy/scipy/blob/main/LICENSES_bundled.txt

 Name               Version    License
Used
 DateTime           5.1        Zope Public License
 attrs              22.2.0     MIT License
 cryptography       40.0.1     Apache Software License; BSD License
 iniconfig          2.0.0      MIT License
 typing_extensions  4.8.0      Python Software Foundation License
 tkcalendar         1.6.1      GNU General Public License v3 (GPLv3)
 mariadb            1.1.6      GNU Lesser General Public License v2 or later (LGPLv2+)

Used for dev/build/test:
 build              1.2.1      MIT License
 coverage           7.2.2      Apache Software License
 pip                24.0       MIT License
 pip-licenses       4.4.0      MIT License
 pytest             7.2.2      MIT License
 pytest-bdd         7.0.0      MIT License
 pytest-cov         4.0.0      MIT License
 pytest-mock        3.12.0     MIT License
 pytest-profiling   1.7.0      MIT License
 toml               0.10.2     MIT License
 python-dotenv      1.0.0      BSD License
 setuptools         59.6.0     MIT License
 tomli              2.0.1      MIT License
 tox                4.4.8      MIT License
 wheel              0.40.0     MIT License
 virtualenv         20.21.0    MIT License

Used?
 Babel              2.12.1     BSD License
Used??
 Mako               1.3.0      MIT License
 MarkupSafe         2.1.3      BSD License
 Pillow             9.5.0      Historical Permission Notice and Disclaimer (HPND)
 cachetools         5.3.0      MIT License
 cffi               1.15.1     MIT License
 chardet            5.1.0      GNU Lesser General Public License v2 or later (LGPLv2+)
 colorama           0.4.6      BSD License
 distlib            0.3.6      Python Software Foundation License
 et-xmlfile         1.1.0      MIT License
 exceptiongroup     1.1.1      MIT License
 filelock           3.10.7     The Unlicense (Unlicense)
 ftputil            5.0.4      BSD License
 gprof2dot          2022.7.29  GNU Lesser General Public License v3 or later (LGPLv3+)
 module-scan        1.0.0      MIT License
 ntplib             0.4.0      MIT License
 numpy              1.24.2     BSD License
 openpyxl           3.1.2      MIT License
 packaging          23.0       Apache Software License; BSD License
 pandas             2.0.0      BSD License
 parse              1.19.1     MIT License
 parse-type         0.6.2      MIT License
 platformdirs       3.2.0      MIT License
 pluggy             1.0.0      MIT License
 prettytable        3.10.0     BSD License
 pycparser          2.21       BSD License
 pycurl             7.45.2     GNU Library or Lesser General Public License (LGPL); MIT License
 pyproject_api      1.5.1      MIT License
 pyproject_hooks    1.0.0      MIT License
 python-dateutil    2.8.2      Apache Software License; BSD License
 pytz               2023.3     MIT License
 recordclass        0.18.4     MIT License
 reportlab          3.6.12     BSD License
 six                1.16.0     MIT License
 tzdata             2023.3     Apache Software License
 wcwidth            0.2.13     MIT License
 zope.interface     6.0        Zope Public License