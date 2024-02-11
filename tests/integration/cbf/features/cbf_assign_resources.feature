@XTP-4599
Feature: Assign resources to CBF subarray


	@skip @XTP-4597 @XTP-4596 @XTP-3324 @XTP-5590
	Scenario: Assign resources to CBF mid subarray
		Given an CBF subarray
		When I assign dishes: SKA001 to the subarray
		Then the CBF subarray must be in IDLE state
