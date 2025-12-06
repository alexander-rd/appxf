Feature: Registration

    Scenario: user registration cycle
    Given admin with an application in status admin initialized
    And admin has stored something in the registry shared configuration
    And admin has stored whatever in the shared configuration

    And user with an application in status unregistered
    And user registry shared confiugration is empty
    And user shared configuration is empty
    And all applications are unlocked

    # The following step consists of (1) generating registration request from
    # user, (2) admin handling the registration request including remote data
    # update and generation of registration response and (3) user handling the
    # registration response including syncing of configuration data
    When user registers the application to admin
    Then user has stored something in the registry shared configuration

# currently taking over steps from manual_bdd_registry.feature