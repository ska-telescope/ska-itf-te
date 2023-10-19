Feature: Dish Structure Simulator

    @AT-1590
    Scenario: Connect to Dish Structure Simulator
        Given the dish structure simulator is deployed in the Mid ITF
        Given its connection details can be retrieved
        When the OPCUA client connects to it
        Then it responds with the expected values