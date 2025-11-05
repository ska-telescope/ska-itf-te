Feature: Telescope scan test
	In this test TMC commands are tested individually. The tester shall be responsible for bring the system back
    to a useable state after any scenario here is executed.

	Scenario: Assign resources
		Given an SUT deployment with 1 subarray
		And a sequence diagrammer has optionally started listening for events
		When I assign resources

	Scenario: Configure scan
		Given an SUT deployment with 1 subarray
		And a sequence diagrammer has optionally started listening for events
		When configure it for a 120 second band 1 scan

	Scenario: Scan
		Given an SUT deployment with 1 subarray
		And a sequence diagrammer has optionally started listening for events
		When I start the scan

	Scenario: End the observation
		Given an SUT deployment with 1 subarray
		And a sequence diagrammer has optionally started listening for events
		When I end the observation

	Scenario: Release resources
		Given an SUT deployment with 1 subarray
		And a sequence diagrammer has optionally started listening for events
		When I release resources
