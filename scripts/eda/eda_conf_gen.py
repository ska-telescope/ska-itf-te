"""Script to generate EDA configuration file. From https://gitlab.com/ska-telescope/ska-dish-lmc/-/snippets/4875213"""

import os
import sys
import argparse

import tango
import yaml


class NoopEvent:
    def push_event(self, event):
        """No-op method to satisfy the Tango event subscription."""
        pass


def generate_eda_config(
    device_trls,
    manager="mid-eda/cm/01",
    archiver="mid-eda/es/01",
    check_subscription=False,
    verbose=False,
) -> str:
    """Generates an EDA configuration file based on the provided Tango TRLs."""
    if "TANGO_HOST" not in os.environ:
        raise RuntimeError("TANGO_HOST is not in the active environment")
    tango_host = os.environ.get("TANGO_HOST")

    if verbose:
        print(f"# TANGO_HOST: {tango_host}")
        print(f"# manager: {manager}")
        print(f"# archiver: {archiver}")
        print(f"# devices: {device_trls}")

    noop_event = NoopEvent()
    eda_data = {"db": tango_host, "manager": manager, "archiver": archiver, "configuration": []}

    try:
        db = None

        for trl in device_trls:
            if verbose:
                print(f"# Generating for device: {trl}")
            dp = tango.DeviceProxy(trl)
            if not db:
                db = dp.get_device_db()
            device_class_name = db.get_class_for_device(trl)
            device_conf = {"class": device_class_name, "attributes": {}}
            attrs = dp.get_attribute_list()

            for i, attr in enumerate(attrs):
                # If enabled skip the attributes we cannot sub to
                if verbose:
                    print(f"\r{i}/{len(attrs)}", end="", flush=True, file=sys.stderr)
                if check_subscription:
                    try:
                        event_id = dp.subscribe_event(
                            attr, tango.EventType.CHANGE_EVENT, noop_event
                        )
                        dp.unsubscribe_event(event_id)
                    except tango.DevFailed:
                        continue
                    except KeyboardInterrupt:
                        sys.exit(1)
                device_conf["attributes"][attr] = {"code_push_event": True}
            eda_data["configuration"].append(device_conf)

        if verbose:
            print()
            print()
        return yaml.dump(eda_data, sort_keys=False)

    except Exception as ex:
        print(f"ERROR: {ex}")
        sys.exit(1)


def main() -> None:
    """Runs the automation to generate the eda config file."""
    parser = argparse.ArgumentParser(
        description="Tool that accepts a list of Tango TRLs and generates an EDA configuration file."
    )
    parser.add_argument(
        "-d",
        "--trl",
        nargs="+",
        dest="device_trls",
        required=True,
        help="List of Tango TRLs for which a configuration file will be generated.",
    )
    parser.add_argument(
        "--manager",
        type=str,
        default="mid-eda/cm/01",
        help="Configuration Manager, default: mid-eda/cm/01",
    )
    parser.add_argument(
        "--archiver",
        type=str,
        default="mid-eda/es/01",
        help="Configuration Archiver, default: mid-eda/es/01",
    )
    parser.add_argument(
        "-s",
        "--check-subscription",
        action="store_true",
        help="If we cannot subscribe to an attribute, skip it, default: False",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print out the progress. Will be commented out for convenience, default: False",
    )
    args = parser.parse_args()

    config_str = generate_eda_config(**vars(args))
    print(config_str)


if __name__ == "__main__":
    main()
