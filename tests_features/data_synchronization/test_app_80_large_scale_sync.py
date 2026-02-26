# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0

# import pytest

# from tests._fixtures import application, appxf_objects

# TODO: CURRENT REFACTORING: move unlocked user/admin pair from registry test
#       to appxf_objects to use in here.

def test_app_80_large_scale_sync(request):
    # TODO: build up large scale application
    pass

    # TODO: add files for each application user:
    #  * SOLE_SURVIVOR will share one information with OVERSEERS (all vaults)
    #    and read all OVERSEER's information
    #  * OVERSEER's are adding files for each "vault" some of them will share
    #    the same vault.
    #  * VAULT_DWELLER's are reading the vault-specific files
    #  * PALADIN goup is on their own.
    #
    # Admin's: 0, 9 and 100
    # SOLE_SURVIVOR: 1
    # PALADIN: 2 to 8
    # OVERSEER: 10,
    #           20, 21,
    #           30, 31, 32,
    #           40,
    #           41, 42,
    #           51, 52, 53 .. 90
    # VAULT DWELLERS: all ID's between 10 and 99 that are not OVERSEER's

    # TODO: For a second round of sync, users will be deleted:
    #  * Admin 9
    #  * Paladins 4 to 8
    #  * 19
    #  * 28, 27
    #  * 37, 36, 35
    #  * 46, .., 43
    #  * 55, 54, 53, 52, 51
    #  * Vaults 6 to 9 are completely dead

    # TODO: For a third round, the same setup will be added again in range 101
    # to 200.

    # 1) Case construction should be split for resource measurements AND for
    #    compatibility.
    # 2) For all use cases, the tests should include:
    #     a) checking current data status
    #     b) write new data and sync cycles according to ROLE based script
    #     c) check data after sync
    #
    # App shall support:
    #   * write data groups
    #   * verify data groups (against old or new ??)
    #   * initiate sync for a role
