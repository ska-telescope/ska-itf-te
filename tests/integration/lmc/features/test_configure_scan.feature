#After deploying the SUT, the LoadDishCfg command Changed DS mode to operate
@AT-2086
Scenario: Test ConfigureScan
    Given DS Operating mode DSOperatingMode STANDBY_LP
    When I command it to LoadDishCfg
    Then DS Operating mode attribute must be in STANDBY_OPERATE