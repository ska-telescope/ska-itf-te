@XTP-4769
Feature: Load dish cfg from the TMC


    @XTP-4771 @XTP-5537 @XTP-4769 @XTP-3324 @XTP-5573
    Scenario: Load dish cfg from the TMC
        Given a TMC central node in adminMode OFFLINE and ON state
        Given a CSP LMC in ONLINE adminMode and OFF state
        When I command it to LoadDishCfg
        Then the DishVccValidationStatus attribute command must be in the OK state