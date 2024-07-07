#After deploying the SUT, the LoadDishCfg command Changed DS mode to operate
#Originating from Jama test https://skaoffice.jamacloud.com/perspective.req#/testCases/972467?projectId=335
@AT-2086
Scenario: Test communications between TMC, LMCs and products of the Telescope
    Scenario: TMC bring telescope to OPERATIONAL state
        Given a Telescope consisting of TMC,LMC,DS,SPF,SPFRx,CBF and SDP
        And the telescope is in ON state
        When I issue a telescope OPERATIONAL command
        Then the telescope products SPFC, DS, SPFRx, CBF and SDP shall be in OPERATIONAL mode
        And TMC API interface shall be updated with OPERATIONAL mode
