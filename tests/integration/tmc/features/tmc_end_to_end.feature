Feature: Telescope end to end signal chain test
	In this test the telescope is controlled via TMC. The telescope is taken from
	the telescope OFF state through loadDishCfg, TelescopeOn, AssignResources, ConfigureScan,
	Scan, EndScan, End and finally, in some scenarios, telescope OFF. I.e. the full signal chain is tested.

	@AT-2305 @AT-1305
	Scenario: End to End signal chain verification via TMC
		Given an SUT deployment with 1 subarray
		And CSP in adminMode online
		When I turn ON the telescope
		And I assign resources for a band 1 scan
		And configure it for a 10 second band 1 scan
		And I start a scan for 10 seconds
		And I end the scan
		And I end the observation
		And I release resources
		And I turn OFF the telescope
		Then the telescope is in the OFF state
		And the respective dataproducts are available on the DPD

	@AT-2349 @AT-3001
	Scenario: End to End signal chain verification via TMC - With HW
		Given an SUT deployment with 1 subarray
		And a sequence diagrammer has optionally started listening for events
		And CSP in adminMode online
		When I turn ON the telescope
		And I assign resources for a band 1 scan
		And configure it for a 120 second band 1 scan
		And I start the scan
		And I end the scan
		And I end the observation
		And I release resources
		And I turn OFF the telescope
		Then the telescope is in the OFF state
		And the respective dataproducts are available on the DPD

	@AT-3322 @AT-3001
	Scenario: End to End signal chain verification via TMC without telescope OFF
		Given an SUT deployment with 1 subarray
		And a sequence diagrammer has optionally started listening for events
		And CSP in adminMode online
		When I turn ON the telescope
		And I assign resources for a band 1 scan
		And configure it for a 120 second band 1 scan
		And I start the scan
		And I end the scan
		And I end the observation
		And I release resources
		Then the telescope is in the released-resources state
		And the respective dataproducts are available on the DPD
	
	@AT-3297 @AT-3001
	Scenario: End to End signal chain verification via TMC with BITE data
		Given an SUT deployment with 1 subarray
		And a sequence diagrammer has optionally started listening for events
		And HPS devices are configured
		And CSP in adminMode online
		When I turn ON the telescope
		And I generate BITE data
		And I assign resources for a band 1 scan
		And I start LSTV replay
		And configure it for a 120 second band 1 scan
		And I start the scan
		And I stop LSTV replay
		And I end the scan
		And I end the observation
		And I release resources
		And I turn OFF the telescope
		Then the telescope is in the OFF state
		And the respective dataproducts are available on the DPD
