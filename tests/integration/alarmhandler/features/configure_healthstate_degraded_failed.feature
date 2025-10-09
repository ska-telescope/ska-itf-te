Feature: SP-3833

	#Verify configured alarm for multiple devices in healthState DEGRADED or FAILED
	@XTP-30405
	Scenario Outline: Configure alarm rule for healthState DEGRADED or FAILED
		Given a mid telescope
		Given an alarm handler
		Given an alarm handler is configured to raise an alarm when the <device1> <device2> healthState 
		When <device1> and <device2> remain in healthState DEGRADED or FAILED
		Then alarm for healthState DEGRADED or FAILED must be raised with UNACKNOWLEDGE state
		Examples:
		    |         device1       | device2             | 
		    |mid-tmc/central-node/0 | mid-tmc/subarray/01 |
