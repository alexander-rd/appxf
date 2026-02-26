# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
import os
from datetime import date
import pytest

from appxf import fileversions
from appxf import logging

from tests.fixtures.env_storage import env_test_directory  # noqa: F401


def test_fileversions_format_yyyyMMdd():
    logging.logging.debug('hello')
    day = date(2023, 4, 1)
    assert (
        fileversions.get_filename('(yyyyMMdd)_(00)_file.txt', day)
        == '20230401_00_file.txt'
    )


def test_fileversions_format_yyyy_cw():
    day = date(2023, 1, 21)
    assert (
        fileversions.get_filename('(yyyy)_CW(ww)_(000)_file.txt', day)
        == '2023_CW04_000_file.txt'
    )


def test_fileversions_format_nodate():
    assert fileversions.get_filename('file_(0000).txt') == 'file_0000.txt'


def test_fileversions_format_onlydate():
    day = date(2023, 4, 1)
    assert fileversions.get_filename('(yyyyMMdd)_file.txt', day) == '20230401_file.txt'


def test_fileversions_locale():
    day = date(2023, 4, 1)
    # Default is English:
    assert (
        fileversions.get_filename('file_(EEEE)_(00).txt', day) == 'file_Saturday_00.txt'
    )
    fileversions.set_locale('de_DE')
    assert (
        fileversions.get_filename('file_(EEEE)_(00).txt', day) == 'file_Samstag_00.txt'
    )


def test_fileversions_notexisting():
    assert fileversions.get_filename('file_(00).txt', existing=True) is None
    # This one is special since it does not contain any versioning:
    assert fileversions.get_filename('(yyyyMMdd)_file.txt', existing=True) is None
    # Not existing by director not existing:
    assert (
        fileversions.get_filename('file_(00).txt', directory='null', existing=True)
        is None
    )


def test_fileversions_format_errors():
    # Unpaired brakets:
    with pytest.raises(ValueError):
        fileversions.get_filename('(')
    with pytest.raises(ValueError):
        fileversions.get_filename(')')
    # Wrongly ordered brakets:
    with pytest.raises(ValueError):
        fileversions.get_filename(')(')
    # Double versions:
    with pytest.raises(ValueError):
        fileversions.get_filename('(0)(00)')
    # Babel date formating error:
    with pytest.raises(AttributeError):
        fileversions.get_filename('(KW)')
    # Infinite loop prevention:
    with pytest.raises(Exception):
        fileversions.get_filename('(yyyy)' * 101)

    assert fileversions.get_filename('file_(00).txt', existing=True) is None
    # This one is special since it does not contain any versioning:
    assert fileversions.get_filename('(yyyyMMdd)_file.txt', existing=True) is None


def test_fileversions_existing(env_test_directory):
    env = env_test_directory
    print(env)
    # Still no files existing:
    assert (
        fileversions.get_filename('file_(00).txt', directory=env['dir'], existing=True)
        is None
    )
    assert (
        fileversions.get_filename('file_00.txt', directory=env['dir'], existing=True)
        is None
    )
    # Drop file
    open(os.path.join(env['dir'], 'file_00.txt'), 'w').close()
    # Check if now existing:
    assert (
        fileversions.get_filename('file_00.txt', directory=env['dir'], existing=True)
        == 'file_00.txt'
    )
    assert (
        fileversions.get_filename('file_(00).txt', directory=env['dir'], existing=True)
        == 'file_00.txt'
    )
    # Check if next version is correct
    assert (
        fileversions.get_filename('file_(00).txt', directory=env['dir'])
        == 'file_01.txt'
    )
