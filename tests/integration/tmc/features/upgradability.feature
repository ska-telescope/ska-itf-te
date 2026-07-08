Feature: Telescope upgradability test

	#This test provides a "prediction" of system behaviour after an upgrade.
	#
	#We want to use commands closely simulating the actions taken while upgrading using FluxCD.
	#
	#The Telescope state should be considered while running this test.
	@AT-3753 @AT-1305
	Scenario: Test upgrade path from the current version of SKA Mid running in Production to the current new tag
		Given a deployment in the ITF of the version of ska-mid currently running on Site with 1 subarray
		When I turn ON the telescope
		And I assign resources
		And configure it for a 10 second band 1 scan
		And I start the scan
		And I end the observation
		And I release resources
		And I upgrade to this tagged pipeline version
		And I assign resources
		And configure it for a 10 second band 1 scan
		And I start the scan
		And I end the observation
		And I release resources
		Then the respective dataproducts are available on the DPD