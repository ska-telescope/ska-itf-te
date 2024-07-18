Feature: Configure the subarray using TMC
	#TODO: Add test ticket tag
	Scenario: Configure the mid telescope subarray using TMC
		Given a TMC
		Given a telescope subarray
		Given a subarray in the IDLE state
		When I configure it for a scan
		Then the subarray must be in the READY state

