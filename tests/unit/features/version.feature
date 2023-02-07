Feature: Unit tests

    These tests check the basics

	@AT-355
	Scenario: Test version of skysimctl package
		Given an imported ska_sky_simulator_controller package
		Then its version is 0.1.0
