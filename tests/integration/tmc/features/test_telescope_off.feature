Feature: Telescope OFF test
	In this test the telescope is turned OFF via the TMC. The various scenarios test
    the telescope OFF command.

	Scenario: Telescope OFF via TMC
        Given an SUT deployment with 1 subarray
        And a sequence diagrammer has optionally started listeing for events
        When I turn OFF the telescope
        Then the telescope is in the OFF state