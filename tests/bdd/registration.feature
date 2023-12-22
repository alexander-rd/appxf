Feature: Registration

    Scenario: Admin Initialization
    Given a fresh tool installation
    When opening the tool
    And no user data exists
    And user initializes as admin
    Then user data shall be generated
    And tool admin certificate shall be generated
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