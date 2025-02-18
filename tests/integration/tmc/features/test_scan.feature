Feature: Telescope scan test
	In this test resources are assigned for a scan and a scan is performed. 
    Once the scan duration elapses, the scan is ended and resources released.
    It is assumed that the telescope is in the ON state

	Scenario: Perform a scan via TMC
        Given an SUT deployment with 1 subarray
		When I assign resources for a band 1 scan
		And configure it for a band 1 scan
		And I start a scan for 120 seconds
		And I end the scan
		And I end the observation
		And I release resources
        Then the respective dataproducts are available on the DPD