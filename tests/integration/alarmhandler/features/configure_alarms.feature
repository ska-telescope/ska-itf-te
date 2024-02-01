Scenario: Configure Alarm for UNKNOWN State
    Given a mid telescope
    Given an alarm handler
    Given an alarm handler is configured to raise an alarm when the <device_name> State <state_value>
    When telescope remains in UNKNOWN state for long
    Then alarm must be raised with UNACKNOWLEDGE state
    Examples:
        |device_name | state_value |
        |CentralNode | UNKNOWN     |