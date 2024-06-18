#After deploying the SUT, the LoadDishCfg command Changed DS mode to operate
#Originating from Jama test https://skaoffice.jamacloud.com/perspective.req#/testCases/972467?projectId=335
@AT-2086
Scenario: Test ConfigureScan
    Given Telescope is on and its subsystems are in STANDBY_LP mode
    When TMC commands the telescope to STANDBY_OPERATE mode
    Then Telescope subsystems must be in STANDBY_OPERATE mode
