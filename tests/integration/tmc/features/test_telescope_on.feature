Feature: Telescope ON test
	In this test the telescope is turned ON via the TMC. The various scenarios test
    the telescope ON command

	@AT-2989 @AT-3001
	Scenario: Telescope ON via TMC
		Given an SUT deployment with 1 subarray
		And a sequence diagrammer has optionally started listeing for events
		And CSP in adminMode online
		When I turn ON the telescope
		Then the telescope is in the ON state