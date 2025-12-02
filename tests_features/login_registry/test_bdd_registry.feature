Feature: Registration

    Scenario: user registration cycle
    Given admin with an application in status admin initialized
    And user with an application in status unlocked but unregistered

# currently taking over steps from manual_bdd_registry.feature