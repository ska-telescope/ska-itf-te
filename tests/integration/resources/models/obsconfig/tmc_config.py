"""Configuration generator for the csp."""
from datetime import timedelta

from ska_tmc_cdm.messages.subarray_node.configure import TMCConfiguration


class TmcConfig:
    """A class representing TMC configuration."""

    def generate_tmc_scan_config(self, scan_duration: float):
        """Generate TMC configuration.

        :param scan_duration: duration of a scan
        :type scan_duration: float
        :return: _description_
        :rtype: TMCConfiguration
        """
        return TMCConfiguration(timedelta(seconds=scan_duration))
