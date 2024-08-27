
Feature: Configure scan via TMC

    Scenario: Configure scan via TMC on 1 subarray in mid
        Given a TMC configured with 1 subarray
        Given a CSP in adminMode online
        When I turn the telescope ON
        When I configure it for a scan
        Then the telescope is ready for scan
        


