Feature: Registration

    Scenario: Tool state after opening
    Given a fresh tool installation
    When opening the tool
    Then user data shall be empty

    Scenario: Tool state after Initialization
    Given a fresh tool installation
    When setting user data
    And setting password
    Then user data shall be available
    And tool security shall be unlocked

    Scnenario: Login after Initialization
    Given an tool with initialized user
    When startion the tool
    Then tool security shall be locked

    # ^^ tried to separate the BDD test cases to simplify the one below

    Scenario: Admin Initialization
    Given an tool with initialized user
    When user decides to initialize as admin

    Scenario: Tool state after admin Initialization
    Given a tool with initialized admin
    When logging in
    Then user data base shall exists
    And no registration is possible

#    Scenario: User Registration
#    Given a fresh tool installation
#    When opening the tool
#    And no user data exists
#    Then user data shall be generated

#    Scenario: Admin Registration
#    Given an initialized user
#    When registering as admin
#    Then