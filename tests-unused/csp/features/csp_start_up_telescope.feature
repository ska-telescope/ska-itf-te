@XTP-3965
Feature: Start up the csp

	@XTP-3964 @XTP-3963 @XTP-3324 @XTP-5573
	Scenario: Start up the csp in mid
		Given a CSP
		When I start up the telescope
		Then the csp must be on