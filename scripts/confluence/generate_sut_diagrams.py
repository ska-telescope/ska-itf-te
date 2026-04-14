import argparse
from pathlib import Path

from ska_ser_skallop.confluence import generate_diagrams_from_config

parser = argparse.ArgumentParser(
    description="Generate diagrams from system dependency configuration file."
)
parser.add_argument(
    "config",
    metavar="configfile",
    type=Path,
    help="The configuration file representing the system",
)


def main():
    args = parser.parse_args()
    config = args.config
    diagrams = generate_diagrams_from_config(config, dest=Path(config).parent)  # type: ignore
    print(f"Created dependencies diagram: {diagrams.dependency_diagram}")
    print(f"Created platform dependents diagram: {diagrams.platform_diagram}")
