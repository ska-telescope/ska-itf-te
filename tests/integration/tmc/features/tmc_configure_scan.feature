Feature: Configure scan via TMC

    Scenario: Configure scan via TMC on 1 subarray in mid
        Given a TMC configured with 1 subarray
        And a CSP in adminMode online
        And a CBF
        And dishes d0001 and d0036
        And a telescope in the ON state
        When I assign resources
        And configure it for a scan
        Then the telescope is ready for scan

        


