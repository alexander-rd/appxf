''' Helping with file versioning.

Versioning is typically done by some date format and adding some index. This
module provides get_filename() to construct corresponging filenames, like:
20230401_v00_file.txt or 2023_CW04.txt (without version index) or file_007.txt
(without date information).
'''
# (C) 2024 github/alexander-rd. Part of APPXF package. MIT license, see LICENSE
# file for details.

import logging
import os.path
import re
import datetime
from babel.dates import format_date


# Setup logging
log = logging.getLogger(__name__)


# TODO: this locale setting below is actually a APPXF language setting. But it
# is not clear how to model this.
#
# 1) Bound to this module. Either as function static as below or as module
#    variable.
#    - this would imply that this locale might be required to be set for other
#      modules as well.
# 2) Bound to language module.
#    - this would imply that language module has to be used.
# 3) APPXF central module. This could also hold other "central" elements like a
#    APPXF logger such that this one can be configured instead of the root
#    logger. When importing APPXF, we would gain access to it (and all sub
#    modules)
# 4) Isn't this configuration?
#    - Cannot bind this to usage of config module by default.
#
# Conclusions: Cross functionals have interdependencies such that (2) is valid
# while the dependency could be hidden or the language modules could be split
# to limit the dependencies. In this context the likely best solution is:
#  * implementing in appxf.language.babel
#  * allow access to set it from appxf, language or any other using module
#    like this one, wrapping appxf.language.babel.set_locale().
#
# Is there a babel "set locale" default??
def set_locale(locale: str):
    log.info('Set locale to {locale}')
    set_locale.locale = locale


# Module variable
set_locale.locale = 'EN'


def get_filename(format: str,
                 date: datetime.date | None = None,
                 directory: str = './',
                 existing: bool = False):
    ''' Get file name from format and date

    babel.date.format_date() is used to get the date related parts of the
    filename. All date formatting from babel can be used. appxf identifies
    the date and version related portions of the file name by () brakets.

    Examples: get_filename('(yyyyMM)_CW(ww)_(00).txt') results in
    '20230103_CW01_00.txt'

    Arguments:
        format -- format string with ()-brakets used to identify date and
        version (00) portions.

    Keyword Arguments:
        date -- datetime generated date. {default: datetime.today()}
        directory -- directory where the file might be present, required
            for versioning. (default: {'./'})
        existing -- Wether to expect the file being existing (True) which
            returns the currently exsiting version or None if not existing or
            to return the next version (False). (default: {False})

    Returns:
        File name with date and version.
    '''
    # Input handling
    if date is None:
        date = datetime.date.today()

    filename = _fill_date_pattern(format, date)
    log.debug(f'Filename is "{filename}" after applying date pattern to '
              f'"{format}" with date={date}')
    filename = _fill_version_pattern(filename, directory, existing)
    return filename


def _fill_date_pattern(format: str, date: datetime.date):
    outstr = format
    # find first opening and closing brackets
    opening_index = -1
    closing_index = -1
    cycle_count = 100
    while True:
        opening = outstr.find('(')
        closing = outstr.find(')')
        # break loop if no brackets are found anymore:
        if opening < 0 and closing < 0:
            break
        # error if opening braket count does not match closing braket count:
        if (opening < 0 and closing >= 0) or (opening >= 0 and closing < 0):
            raise ValueError(
                f'Format string {format} does not have matching braket for '
                f'{"opening" if opening > 0 else "closing"} braket at '
                f'position {opening if opening > 0 else closing}.')
        if opening > closing:
            raise ValueError(
                f'Format string {format} close braket before opening.')
        else:
            # opening >= 0, opening > closing and opening != closing implies
            # closing > 0
            datestr = outstr[(opening+1):(closing)]
            # skip zeros (index part)
            if datestr.find('0') >= 0:
                # Error if we find this twice:
                if opening_index >= 0 or closing_index >= 0:
                    raise ValueError(
                        f'Format string {format} contains two indications '
                        'for indexing file versions like "(00)". '
                        'Only one is expected.')
                else:
                    opening_index = opening
                    closing_index = closing
                    # Overwrite with non-braket to find next format string in
                    # next loop
                    outstr = (outstr[:opening] + '.'
                              + datestr + '.'
                              + outstr[closing+1:])
            else:
                datestr = format_date(date, datestr, locale=set_locale.locale)
                outstr = outstr[:opening] + datestr + outstr[closing+1:]
        # avoid freezing programs due to programming errors
        cycle_count -= 1
        if cycle_count <= 0:
            assert cycle_count > 0, (
                'Implementation error: format string '
                f'"{format}" lead to infinite loop.')
    # revert indexing brakets
    if (opening_index >= 0):
        outstr = (outstr[:opening_index] + '('
                  + outstr[opening_index+1:closing_index] + ')'
                  + outstr[closing_index+1:])
    return outstr


def _fill_version_pattern(filename: str, dir: str, existing: bool):
    # Note that _fill_date_pattern must always be called before. It contains
    # the error handling for brakets. After that execution, only one braked
    # pair is remaining for versioning (or none).
    opening = filename.find('(')
    closing = filename.find(')')
    # If there is no versioning pattern, we can return:
    if opening < 0 or closing < 0:
        if existing and (not os.path.exists(os.path.join(dir, filename))):
            return None
        else:
            return filename
    # If there is one, this is the regexp to match files and see the
    regex = re.compile(filename[:opening]+r'(\d+)'+filename[closing+1:])
    version = -1
    # cycle filenames in directory:
    if os.path.exists(dir):
        for file in os.listdir(dir):
            match = re.fullmatch(regex, file)
            if match is None:
                continue
            else:
                # No error handling, int() should convert always since group is
                # \d+
                this_version = int(match.group(1))
                if this_version > version:
                    version = this_version
    else:
        # Nothing to do, file does not exist if directory does not exist
        pass

    if existing and version < 0:
        # We cannot return a file name if an existing file is expected
        return None
    elif not existing:
        # We need to use the next version:
        version += 1
    versionstr = ('{:0' + str(closing-opening-1) + '}').format(version)
    return filename[:opening] + versionstr + filename[(closing+1):]
