
# This test provides a "prediction" of system behaviour after an upgrade.
# We want to use commands closely simulating the actions taken while upgrading using FluxCD.
# The Telescope state should be considered while running this test.

# Given a running deployment in the ITF of the version of ska-mid currently in ska-mid-helmreleases main with 1 subarray

Feature: Telescope upgradability test

	@AT-3753 @AT-1305
	Scenario: Test upgrade path from the current version of SKA Mid running in Production to the current new tag
		Given an SUT deployment with 1 subarray
		And the SUT deployment is the version of ska-mid currently in ska-mid-helmreleases main
		When I assign resources
		And configure it for a 120 second band 1 scan
		And I start the scan
		And I end the observation
		And I release resources
		And I upgrade to this tagged pipeline version
		And I assign resources
		And configure it for a 120 second band 1 scan
		And I start the scan
		And I end the observation
		And I release resources
		Then the respective dataproducts are available on the DPD
