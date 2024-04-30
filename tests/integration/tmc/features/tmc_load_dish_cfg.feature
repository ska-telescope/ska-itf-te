@AT-2027 @AT-2026 @SKB-338
Scenario: Load dish cfg from the TMC
    Given a CSP LMC in ONLINE adminMode and OFF state
    Given a TMC central node in adminMode OFFLINE and ON state
    When I command it to LoadDishCfg
    Then the DishVccValidationStatus attribute command must be in the OK state

@AT-2027 @AT-2026 @SKB-338
Scenario: Test fixture teardown
    Given a fixture
    When I command it do something
    Then the value is set