Feature: SP-3833

	#Verify configured alarm for multiple devices in healthState DEGRADED
	@XTP-30405
	Scenario Outline: Configure alarm rule for healthState DEGRADED
		Given a mid telescope
		Given an alarm handler
		Given an alarm handler is configured to raise an alarm when the <device1> <device2> healthState 
		When <device1> and <device2> remain in healthState DEGRADED for long
		Then alarm for healthState DEGRADED must be raised with UNACKNOWLEDGE state
		Examples:
		    |         device1       | device2             | 
		    |mid-tmc/central-node/0 | mid-tmc/subarray/01 |
