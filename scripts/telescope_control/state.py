"""Telescope state reporting and control."""
import argparse
import logging

from utils.telescope_teardown import TelescopeHandler

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(
    prog="Telescope control", description="Telescope monitoring and manipulation", epilog=""
)
parser.add_argument("-p", "--print-state", action="store_true", help="Print telescope state")
parser.add_argument("-n", "--namespace", help="Specify namespace to execute against")
parser.add_argument(
    "-d", "--dish-ids", help="Provide dish ID's as a space seperated string e.g. 'SKA001 SKA036'"
)
parser.add_argument(
    "-t", "--teardown", action="store_true", help="Teardown the telescope to base state"
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
        if args.print_state:
            logger.info(f"Current telescope state: {telescope.get_current_state()}")

        if args.teardown:
            telescope.teardown()
    else:
        print("Provide both namespace and dish ID's")


if __name__ == "__main__":
    main()
