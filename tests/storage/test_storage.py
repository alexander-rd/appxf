# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""Test Storage Base Class

See specific test files for storage OBJECT related tests and implementation
specific tests.
"""

# TODO: there should be a test case that tries to get/get_factory/construct a
# SecurePrivate storage after it was already created. Suspicion is that a
# second get may get the base storage but this already being a SecureStorage
# and then wrapping through SecureStorage again. -- -- This should be covered
# by __init__ never reached and __init__being blocked once a secure stroage is
# already generated. But what's with the use case where a base storage is
# already present - it should also not be possible to get/construct a
# SecureStorage on that. While this is the normal way via __init__, __init__
# should be blocked in general >> never to be used since it may circumvent the
# registration.

from __future__ import annotations

from typing import Callable


def test_storage_simple_abstract_derivative():
    from appxf.storage import Storage

    # Verify properties of Storage before touching anything
    assert Storage.__abstractmethods__

    # Derivation One
    class DerivateOne(Storage):
        pass

    assert DerivateOne.__abstractmethods__


def test_storage_simple_derivative():
    from appxf.storage import Storage

    # Derivation One
    class DerivateOne(Storage):
        @classmethod
        def get(
            cls,
            name: str,
            location: str,
            storage_init_fun: Callable[..., Storage],
            user: str = "",
        ) -> Storage:
            return super().get(
                name=name,
                location=location,
                storage_init_fun=lambda: DerivateOne(name, location),
            )

        def exists(self) -> bool:
            return False

        def store_raw(self, data: object, meta: str = ""):
            pass

        def load_raw(self, meta: str = "") -> object:
            return None

    # this checks for behavior on root storage and preset keys
    assert not DerivateOne.__abstractmethods__

    storage = DerivateOne("test")
    # no user and no location was defined:
    assert storage.user == ""
    assert storage.location == ""
    assert storage.id() == "DerivateOne(): test"


def test_storage_copmlex_derivative():
    from appxf.storage import Storage

    # We test proper collection of keywords through multiple instances AND
    # assigning the correct root storage
    class DerivateOneAbstract(Storage):
        pass

    class DerivativeTwoRoot(DerivateOneAbstract):
        @classmethod
        def get(
            cls,
            name: str,
            location: str,
            storage_init_fun: Callable[..., Storage],
            user: str = "",
        ) -> Storage:
            return super().get(
                name=name,
                location=location,
                storage_init_fun=lambda: DerivativeTwoRoot(name, location),
            )

        def exists(self) -> bool:
            return False

        def store_raw(self, data: object, meta: str = ""):
            pass

        def load_raw(self, meta: str = "") -> object:
            return None

    class DerivativeThree(DerivativeTwoRoot):
        pass

    # verify root and abstract properties
    assert DerivateOneAbstract.__abstractmethods__
    assert not DerivativeTwoRoot.__abstractmethods__
    assert not DerivativeThree.__abstractmethods__
