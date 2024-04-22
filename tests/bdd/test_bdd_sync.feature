Feature: Synchronization

    Scenario Outline: Self Testing
    Given Locations [A]
    And Location A is using <method>
    Then there is no data in A
    When A writes "some data" into some_data
    Then A contains "some data" in some_data

    Examples:
    | method               |
    | Default              |
    | SecurePrivateStorage |
    | SecureSharedStorage  |


    Scenario: Simple Initialization
    Given Locations [A, B]
    When A writes "some data" into some_data
    And Synchronizing A with B
    Then Data in A matches data in B

    Scenario: Update Loop
    Given Locations [A, B]
    And A writes "some data" into some_data
    And Synchronizing A with B
    When A writes "some new data" into some_data
    And Synchronizing A with B
    Then B contains "some new data" in some_data

    Scenario: Synchronization round trip
    Given Locations [A, B, C]
    And A writes "some data" into some_data
    And Synchronizing A with B
    And Synchronizing B with C
    Then Data in A matches data in B
    And Data in A matches data in C
    And Data in B matches data in C

    When A writes "new data from A" into some_data
    And Synchronizing A with B
    And Synchronizing B with C
    Then B contains "new data from A" in some_data
    And C contains "new data from A" in some_data

    When C writes "new data from C" into some_data
    # Loations are provided in orders as above to cover the backwards direction
    # in code.
    And Synchronizing B with C
    And Synchronizing A with B
    Then B contains "new data from C" in some_data
    And A contains "new data from C" in some_data


    Scenario Outline: Synchronization Round Trip with Secures Storage
    Given Locations [A, B, C]
    And Location A is using <methodA>
    And Location B is using <methodB>
    And Location C is using <methodC>
    And A writes "some data" into some_data
    And Synchronizing A with B
    And Synchronizing B with C
    Then C contains "some data" in some_data

    # TODO: Testing SecureSharedStorage is a fake since the sync
    # algorithm does not use the storage method. It uses the location's _store
    # and _load directly.

    Examples:
    | methodA                 | methodB                 | methodC                 |
    | SecurePrivateStorage    | SecurePrivateStorage    | SecurePrivateStorage    |
    | SecurePrivateStorage    | SecureSharedStorage     | SecurePrivateStorage    |