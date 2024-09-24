Feature: Perform scan via TMC

    Scenario: Perform a single scan end-to-end via TMC
        Given a TMC configured with 1 subarray
        And a CSP in adminMode online
        And a CBF
        And dishes d0001 and d0036
        And a telescope in the ON state
        When I assign resources
        And configure it for a scan
        And I start a scan for 10s
        And I end the scan
        And I end the observation
        And I release resources
        And I turn OFF the telescope
        Then the telescope is in the OFF state
        


