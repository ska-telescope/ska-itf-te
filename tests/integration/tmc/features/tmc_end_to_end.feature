Feature: Perform a single scan end-to-end via TMC

    Scenario: Perform a single scan end-to-end via TMC
        Given an SUT deployment with 1 subarray and dishes SKA001 and SKA036
        And CSP in adminMode online
        When I turn ON the telescope
        And I assign resources
        And configure it for a scan
        And I start a scan for 10s
        And I end the scan
        And I end the observation
        And I release resources
        And I turn OFF the telescope
        Then the telescope is in the OFF state
        And the respective dataproducts are available on the DPD
        


