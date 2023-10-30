@XTP-3969
Feature: Start up the cbf

	@skip @XTP-3968 @XTP-3967 @XTP-3324 @XTP-5590
	Scenario: Start up the cbf in mid
		Given an CBF
		When I start up the telescope
		Then the cbf must be on