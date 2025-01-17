Feature: Telescope end to end signal chain test
	In this test the telescope is controlled via TMC. The telescope is taken from
	the telescope OFF state through loadDishCfg, TelescopeOn, AssignResources, ConfigureScan,
	Scan, EndScan, End and finally telescope OFF. I.e. the full signal chain is tested.

	@AT-2305 @AT-1305
	Scenario: End to End signal chain verification via TMC
		Given an SUT deployment with 1 subarray
		And CSP in adminMode online
		When I turn ON the telescope
		And I assign resources
		And configure it for a scan
		And I start a scan for 10 seconds
		And I end the scan
		And I end the observation
		And I release resources
		And I turn OFF the telescope
		Then the telescope is in the OFF state
		And the respective dataproducts are available on the DPD

	@AT-2349 @AT-1305
	Scenario: End to End signal chain verification via TMC - With HW
		Given an SUT deployment with 1 subarray
		And CSP in adminMode online
		When I turn ON the telescope
		And I assign resources
		And configure it for a scan
		And I start a scan for 120 seconds
		And I end the scan
		And I end the observation
		And I release resources
		And I turn OFF the telescope
		Then the telescope is in the OFF state
		And the respective dataproducts are available on the DPD