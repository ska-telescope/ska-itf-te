"""Telescope state reporting and control."""
import argparse
import logging

from utils.telescope_teardown import TelescopeHandler, TelescopeState
from ska_control_model._dev_state import DevState
from ska_control_model import ObsState
from utils.enums import DishMode

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(
    prog="Telescope control", description="Telescope monitoring and manipulation", epilog=""
)
parser.add_argument("-p", "--print-state", action="store_true", help="Print telescope state")
parser.add_argument("--print-base-state", action="store_true", help="Print telescope state")
parser.add_argument("-n", "--namespace", help="Specify namespace to execute against")
parser.add_argument(
    "-d", "--dish-ids", help="Provide dish ID's as a space seperated string e.g. 'SKA001 SKA036'"
)
parser.add_argument(
    "-t", "--teardown", action="store_true", help="Teardown the telescope to base state"
)
parser.add_argument(
    "-c", "--central-node-base-state", help="Provide the base subarray node state e.g. READY"
)
parser.add_argument(
    "-s", "--subarray-base-state", help="Provide the base subarray node state e.g. READY"
)
parser.add_argument(
    "-b", "--dish-base-state", help="Provide the base dish state e.g. STANDBY_FP"
)
args = parser.parse_args()


def main(args=args):
    """.

    :param args: _description_, defaults to args
    :type args: _type_, optional
    """
    
    if args.namespace and args.dish_ids:
        dish_ids = args.dish_ids.split(" ")
        telescope = TelescopeHandler(args.namespace, dish_ids)
        initial_dish_base_state = {dish_id: DishMode.STANDBY_LP for dish_id in dish_ids}
        base_state = TelescopeState(dishes=initial_dish_base_state)

        if args.central_node_base_state:
            state_name = args.central_node_base_state.upper()
            base_state.central_node = DevState[state_name]
            logger.info("Set cn base state")

        if args.subarray_base_state:
            state_name = args.subarray_base_state.upper()
            base_state.subarray = ObsState[state_name]
            logger.info("Set subarray base state")
                
        if args.dish_base_state:
            state_name = args.dish_base_state.upper()
            dish_base_state = {dish_id: DishMode[state_name] for dish_id in dish_ids}
            base_state.dishes = dish_base_state
            logger.info("Set dish base state")

        telescope.telescope_base_state = base_state
                
        if args.print_state:
            logger.info(f"Current telescope state: {telescope.get_current_state()}")

        if args.print_base_state:
            logger.info(f"Current base state: {telescope.telescope_base_state}")

        if args.teardown:
            telescope.teardown()
    else:
        print("Provide both namespace and dish ID's")


if __name__ == "__main__":
    main()
