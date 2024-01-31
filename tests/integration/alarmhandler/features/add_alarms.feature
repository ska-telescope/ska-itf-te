@XTP-30174
Scenario: Configure TMC Alarms
    Given a TMC
    Given an alarm handler
    When I configure alarms with <alarm_rule_file> for TMC using alarm configurator tool
    Then TMC alarms are configured successfully
    Examples:
    |alarm_rule_file     |
    | alarm_file1.txt    |