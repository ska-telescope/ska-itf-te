Scenario: Configure TMC alarms
    Given a TMC
    Given an alarm handler
    When I configure alarms for TMC using alarm configurator tool
    Then TMC alarms are successfully configured