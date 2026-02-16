# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0
Feature: Registration

    Scenario: user registration cycle
    Given admin with an application in status admin initialized
    And user with an application in status unregistered
    And all applications are unlocked

    # Note: the unlocking is required for the lines below, otherwise an updated
    # config cannot be stored onto the file system:
    And admin is storing something in the registry shared configuration
    And admin is storing whatever in the shared configuration
    # Verify user state being unfilled:
    And user registry shared configuration is empty
    And user shared configuration is empty

    # The following step consists of (1) generating registration request from
    # user, (2) admin handling the registration request including remote data
    # update and generation of registration response and (3) user handling the
    # registration response including syncing of configuration data
    When user registers the application to admin
    Then user has stored something in the registry shared configuration
    # TODO: following line is not yet operational since sync behavior after
    # registration must still be defined and verified:
#    And user has stored whatever in the shared configuration

# currently taking over steps from manual_bdd_registry.feature