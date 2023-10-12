from pytest_bdd import given, scenario, then

@scenario(
    "features/ds_sim_connection.feature",
    "Connect to Dish Structure Simulators post-deployment",
)
def test_connect_to_ds_sim():
    """Connect to Dish Structure Simulators post-deployment."""


