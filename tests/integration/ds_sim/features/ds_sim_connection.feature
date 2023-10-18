@AT-1590
Scenario: Connect to Dish Structure Simulators post-deployment
    Given the dish structure simulator is deployed in the Mid ITF
    And its connection details can be retrieved
    When the OPCUA client connects to it
    Then it responds with the expected values