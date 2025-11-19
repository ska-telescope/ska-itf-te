Feature: Command the telescope via TMC step by step. 
	These scenarios are purely for convenience when wanting to send commands step by step to TMC. 
	The tester shall be responsible for bringing the system back to a useable state before executing any scenario here.
	Success is checked within the final 'When' step itself.

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
