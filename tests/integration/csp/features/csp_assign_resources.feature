@XTP-4634
Feature: Assign resources to CSP subarray


	@skip @XTP-4636 @XTP-5537 @XTP-4635 @XTP-3324 @XTP-5573
	Scenario: Assign resources to CSP mid subarray
		Given a CSP subarray
		When I assign resources to it
		Then the CSP subarray must be in IDLE state

	@skip @XTP-5787 @XTP-5537 @XTP-4635 @XTP-3324
	Scenario: Release resources assigned to an CSP mid subarray
		Given a CSP subarray in IDLE state
		When I release all resources assigned to it
		Then the CSP subarray must be in EMPTY state

	@skip @XTP-20082 @XTP-5537 @XTP-4635 @XTP-3324
	Scenario: Abort assigning CSP
		Given an subarray busy assigning
		When I command it to Abort
		Then the subarray should go into an aborted state

	@skip @XTP-20131
	Scenario: Abort assigning CSP Low
		Given an subarray busy assigning
		When I command it to Abort
		Then the subarray should go into an aborted state