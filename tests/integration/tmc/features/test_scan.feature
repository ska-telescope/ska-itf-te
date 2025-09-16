Feature: Telescope scan test
	In this test resources are assigned for a scan and a scan is performed. 
	Once the scan duration elapses, the scan is ended and in some scenarios resources are released.
	It is assumed that the telescope is in the ON state

	@AT-2998 @AT-3001
	Scenario: Perform a scan via TMC
		Given an SUT deployment with 1 subarray
		And a sequence diagrammer has optionally started listening for events
		When I assign resources for a band 1 scan
		And configure it for a band 1 scan
		And I start a scan for 120 seconds
		And I end the scan
		And I end the observation
		And I release resources
		Then the respective dataproducts are available on the DPD

	Scenario: Perform multiple scans via TMC without releasing resources
		Given an SUT deployment with 1 subarray
		And a sequence diagrammer has optionally started listening for events
		When I assign resources for a band 1 scan
		And configure it for a band 1 scan
		And I execute 3 120 second scans without reconfiguring or releasing resources
		Then the respective dataproducts are available on the DPD
