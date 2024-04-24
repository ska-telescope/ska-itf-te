@AT-2027 @AT-2026 @SKB-338
Scenario: Load dish cfg from the TMC
    Given a TMC central node in adminMode OFFLINE and ON state
    Given a CSP LMC in ONLINE adminMode and OFF state
    When I command it to LoadDishCfg
    Then the DishVccValidationStatus attribute command must be in the OK state