#! .venv/bin/python3
import os
from tango import DeviceProxy
from dataclasses import dataclass
from time import sleep
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.integration.tmc.conftest import wait_for_event
import subprocess, signal
import re
import argparse

import numpy as np

# Layout of the "spectrometer_spectrum_result" attribute (8202 elements).
# Two gated blocks (noise diode ON then OFF) follow a 2 element header.
# Each block is four consecutive 1025 channel products: XX, YY, XY_re, XY_im.
SPECTRUM_HEADER_LEN = 2
SPECTRUM_N_CHANNELS = 1025
SPECTRUM_BLOCK_LEN = 4 * SPECTRUM_N_CHANNELS
SPECTRUM_RESULT_LEN = SPECTRUM_HEADER_LEN + 2 * SPECTRUM_BLOCK_LEN

DEFAULT_THROTTLE_INTERVAL = 100
DEFAULT_NUM_PACKETS = 50
DEFAULT_CAPTURE_INTERVAL = 1.0

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
# console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)


@dataclass
class AttenuationLevels:
    b2PolHAttenuation1: float
    b2PolHAttenuation2: float
    b2PolVAttenuation1: float
    b2PolVAttenuation2: float


@dataclass
class SpectrumCapture:
    """
    A single gated spectrometer readout, split into its products.

    Every product array has shape (2, 1025): row 0 is the noise diode ON
    gate, row 1 is the noise diode OFF gate. Values are raw accumulator
    counts, no dB conversion applied.
    """

    timestamp: int
    xx: np.ndarray
    yy: np.ndarray
    xy_re: np.ndarray
    xy_im: np.ndarray
    raw: np.ndarray

    @property
    def xy_magnitude(self) -> np.ndarray:
        return np.sqrt(np.square(self.xy_re) + np.square(self.xy_im))

    @property
    def xy_phase_deg(self) -> np.ndarray:
        return np.rad2deg(np.arctan2(self.xy_im, self.xy_re))

    @staticmethod
    def to_db(product: np.ndarray) -> np.ndarray:
        """Convert an auto product to dB, flooring zeros to 1 count."""
        return 10 * np.log10(np.where(product != 0, product, 1))


class SPFRxSATExecutor:

    def __init__(self, tango_host: str = None, sat_environment: str = None, dish_id: str = None, spfrx_ip: str = None):
        if not sat_environment:
            raise ValueError("SPFRx SAT_ENVIRONMENT is not set.")
        
        if sat_environment == "ITF" and not spfrx_ip:
            raise ValueError("Automatic SPFRx IP is not supported for ITF environment. Please provide SPFRx IP.")

        if not dish_id:
            raise ValueError("SPFRx DISH_ID is not set.")
        
        if not re.match(r"SKA\d+", dish_id):
            raise ValueError("SPFRx DISH_ID must be in the format SKAXXX.")

        if not tango_host:
            # Find the appropriate TANGO_HOST based on the SAT_ENVIRONMENT and DISH_ID
            if sat_environment == "ITF":
                tango_host = f"tango-databaseds.staging-dish-lmc-{dish_id.lower()}.svc.miditf.internal.skao.int:10000"
            elif sat_environment == "Production":
                tango_host = f"tango-databaseds.dish-lmc-{dish_id.lower()}.svc.{dish_id.lower()}.mid.internal.skao.int:10000"
            else:
                raise ValueError(f"Unknown SAT_ENVIRONMENT: {sat_environment}. Supported values are 'ITF' and 'Production'.")

        self.dish_tango_host = tango_host
        self.dish_id = dish_id
        self.spfrx_ip = spfrx_ip if spfrx_ip else f"10.160.{int(dish_id.split('SKA')[1])}.5"

        self.spfrx_controller_trl = f"{tango_host}/{dish_id}/spfrxpu/controller"
        self.pktcap_trl = f"{tango_host}/{dish_id}/spfrxpu/pktcap"
        self.eth100g_trl = f"{tango_host}/{dish_id}/spfrxpu/100gigeth"
        self.band_processor_trl = f"{tango_host}/{dish_id}/spfrxpu/bandprocessor123-12"

        self.spfrx_controller = DeviceProxy(self.spfrx_controller_trl)
        self.pktcap = DeviceProxy(self.pktcap_trl)
        self.eth100g = DeviceProxy(self.eth100g_trl)
        self.band_processor = DeviceProxy(self.band_processor_trl)

        # The 3s pytango default is too tight for the spectrometer retrieval
        # and the 8202 element spectrum read.
        self.spfrx_controller.set_timeout_millis(5000)
        self.pktcap.set_timeout_millis(5000)

        self.initial_attenuation_levels = AttenuationLevels(
            b2PolHAttenuation1=10.0,
            b2PolHAttenuation2=10.0,
            b2PolVAttenuation1=10.0,
            b2PolVAttenuation2=10.0,
        )

        self.new_attenuation_levels = AttenuationLevels(
            b2PolHAttenuation1=15.0,
            b2PolHAttenuation2=15.0,
            b2PolVAttenuation1=15.0,
            b2PolVAttenuation2=15.0,
        )

    def check_data_flow(self) -> dict:
        # Implementation of the data flow check logic
        result = {
            "TxFrameOctetsOK_initial": "",
            "TxFrameOctetsOK_at_eval": "",
            "data_flowing": False,
        }
        TxFrameOctetsOK_initial = self.eth100g.read_attribute("TxFrameOctetsOK").value
        sleep(10)  # Wait for 10 seconds before checking the attribute again
        TxFrameOctetsOK_at_eval = self.eth100g.read_attribute("TxFrameOctetsOK").value

        result["TxFrameOctetsOK_initial"] = TxFrameOctetsOK_initial
        result["TxFrameOctetsOK_at_eval"] = TxFrameOctetsOK_at_eval

        if TxFrameOctetsOK_at_eval > TxFrameOctetsOK_initial:
            result["data_flowing"] = True
            return result

        return result

    def set_attenuation_levels(self, attenuation_levels: AttenuationLevels):
        # Implementation of the attenuation level setting logic
        self.spfrx_controller.b2PolHAttenuation1 = attenuation_levels.b2PolHAttenuation1
        self.spfrx_controller.b2PolHAttenuation2 = attenuation_levels.b2PolHAttenuation2
        self.spfrx_controller.b2PolVAttenuation1 = attenuation_levels.b2PolVAttenuation1
        self.spfrx_controller.b2PolVAttenuation2 = attenuation_levels.b2PolVAttenuation2

    def get_attenuation_levels(self) -> AttenuationLevels:
        # Implementation of the attenuation level retrieval logic
        return AttenuationLevels(
            b2PolHAttenuation1=self.spfrx_controller.b2PolHAttenuation1,
            b2PolHAttenuation2=self.spfrx_controller.b2PolHAttenuation2,
            b2PolVAttenuation1=self.spfrx_controller.b2PolVAttenuation1,
            b2PolVAttenuation2=self.spfrx_controller.b2PolVAttenuation2,
        )

    def set_noise_source(self, noise_source: int):
        # Implementation of the noise source setting logic
        self.spfrx_controller.switchSource(noise_source)

    def configure_band(self, band: int):
        # Implementation of the band setting logic and operatingmode check

        if band == 1:
            logger.info(f"Configuring band {band} with PPS Sync.")
            self.spfrx_controller.configureband1(True)
        elif band == 2:
            logger.info(f"Configuring band {band} with PPS Sync.")
            self.spfrx_controller.configureband2(True)
        else:
            raise ValueError(f"Invalid band: {band}. Only bands 1 and 2 are supported.")

        wait_for_event(
            self.spfrx_controller,
            "configuredBand",
            band,
            timeout=30.0,
        )
        wait_for_event(
            self.spfrx_controller,
            "operatingMode",
            3,
            timeout=30.0,
        )
        return True

    def _configure_packet_capture(
        self,
        throttle_interval: int = DEFAULT_THROTTLE_INTERVAL,
        num_packets: int = DEFAULT_NUM_PACKETS,
    ):
        """
        Arm the gated spectrometer on the pktcap device.

        :param throttle_interval: Spectrometer throttle interval in ms.
        :param num_packets: Packets to capture each throttle interval.
        """
        self.pktcap.write_attribute("spectrometer_throttle_interval", throttle_interval)
        self.pktcap.write_attribute("spectrometer_num_packets", num_packets)

        # Route the spectrometer results through the lightweight bridge,
        # then enable the spectrometer. The enable gate is a controller
        # command (SpectrometerCtrl), not a pktcap one.
        self.pktcap.command_inout("spectrometer_set_bridge", 1)
        self.spfrx_controller.command_inout("SpectrometerCtrl", True)
        sleep(10)

    def capture_packets(
        self,
        n_captures: int = 1,
        interval: float = DEFAULT_CAPTURE_INTERVAL,
        throttle_interval: int = DEFAULT_THROTTLE_INTERVAL,
        num_packets: int = DEFAULT_NUM_PACKETS,
        configure: bool = True,
    ) -> list[SpectrumCapture]:
        """
        Capture the SPFRx datastream via the pktcap device.

        Each capture triggers a spectrometer retrieval, reads the resulting
        spectrum attribute and unpacks it into a SpectrumCapture.

        :param n_captures: Number of spectra to capture.
        :param interval: Seconds to wait between captures.
        :param throttle_interval: Spectrometer throttle interval in ms.
        :param num_packets: Packets to capture each throttle interval.
        :param configure: Arm the spectrometer before capturing. Set False
                          when it has already been configured.
        :returns: The captured spectra, oldest first.
        """
        if configure:
            self._configure_packet_capture(throttle_interval, num_packets)

        captures = []
        for capture in range(n_captures):
            if capture:
                sleep(interval)

            # Go through command_inout/read_attribute rather than
            # attribute-style access: the latter resolves names via the
            # proxy's cached command list and masks any DevFailed as an
            # AttributeError.
            self.pktcap.command_inout("spectrometer_retrieve_result")
            raw = self.pktcap.read_attribute("spectrometer_spectrum_result").value

            captures.append(self.parse_spectrum(raw))
        sleep(10)
        self.spfrx_controller.command_inout("SpectrometerCtrl", False)

        return captures

    @staticmethod
    def parse_spectrum(raw) -> SpectrumCapture:
        """
        Unpack a raw spectrometer_spectrum_result into its products.

        :param raw: The raw attribute value.
        :returns: The unpacked SpectrumCapture.
        :raises ValueError: If the result is empty or the wrong length.
        """
        if raw is None:
            raise ValueError("pktcap returned an empty spectrum result")

        raw = np.asarray(raw)
        if raw.size != SPECTRUM_RESULT_LEN:
            raise ValueError(
                f"Expected {SPECTRUM_RESULT_LEN} element spectrum result, "
                f"got {raw.size}"
            )

        # Stack the noise diode ON and OFF gates so each product is (2, 1025).
        def product(index: int) -> np.ndarray:
            def gate(block: int) -> np.ndarray:
                start = (
                    SPECTRUM_HEADER_LEN
                    + block * SPECTRUM_BLOCK_LEN
                    + index * SPECTRUM_N_CHANNELS
                )
                return raw[start : start + SPECTRUM_N_CHANNELS]

            return np.array([gate(0), gate(1)])

        return SpectrumCapture(
            timestamp=int(raw[0]),
            xx=product(0),
            yy=product(1),
            xy_re=product(2),
            xy_im=product(3),
            raw=raw,
        )

    def validate_spfrx_output(self, attenuation_levels: AttenuationLevels):
        # Implementation of the SPFRx output validation logic
        pass

    def generate_sat_report(self):
        # Implementation of the SAT report generation logic
        pass

    def start_plotter(self):
        plotter_process = subprocess.Popen(
            [
            "make",
            "spfrx-plotter",
            f"SPFRX_TANGO_HOST={self.dish_tango_host}",
            f"SPFRX_ADDRESS={self.spfrx_ip}",
            f"ARGS=--device={self.dish_id}",
            ],
            cwd=os.path.expanduser("~/ska-mid-dish-spfrx-talondx-console"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
            close_fds=True,
        )
        returncode = plotter_process.poll()

        if returncode is not None and returncode != 0:
            stdout, stderr = plotter_process.communicate()
            print("STDOUT:")
            print(stdout)
            print("STDERR:")
            print(stderr)
            return returncode
        return True

    def stop_plotter(self):
        # Close plotter
        subprocess.run(
            ["docker", "stop", "spfrx-plotter"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.spfrx_controller.command_inout("SpectrometerCtrl", False)
        return True
    
    def execute(self, band: int):
        # Implementation of the SAT execution logic
        
        # Initialisation
        logger.info("Initialising.")
        logger.info(f"Current band: {self.spfrx_controller.configuredBand}")
        logger.info(f"Current pps deviation: {self.band_processor.pps_deviation}")
        logger.info(f"Current kLocked: {self.spfrx_controller.isKLocked}")
        logger.info(f"Current Operating mode: {self.spfrx_controller.operatingMode}")
        logger.info(f"Checking data flow")
        logger.info(f"Data flow check result: {self.check_data_flow()}")
        logger.info("Setting operating mode to STANDBY.")
        self.spfrx_controller.setstandbymode()
        
        logger.info("Setting attenuation levels to initial values.")
        self.set_attenuation_levels(self.initial_attenuation_levels)
        logger.info(f"Current attenuation levels: {self.get_attenuation_levels()}")
        logger.info("Setting noise source to 0")
        self.set_noise_source(0)
        logger.info("Initialisation complete.")

        # SAT Flow
        self.configure_band(band)
        # sleep(10)
        logger.info(f"Current band: {self.spfrx_controller.configuredBand}")
        logger.info(f"Current pps deviation: {self.band_processor.pps_deviation}")
        logger.info(f"Current kLocked: {self.spfrx_controller.isKLocked}")
        logger.info(f"Current Operating mode: {self.spfrx_controller.operatingMode}")
        logger.info(f"Checking data flow")
        logger.info(f"Data flow check result: {self.check_data_flow()}")

        # Manual verification of the spectrum
        user_input = input(f"Is the spectrum correct for the following attenuation levels: {self.get_attenuation_levels()} (Y/N): ").strip().upper()
        if user_input != "Y":
            logger.info(f"Result not accepted. SAT failed for band {band}.")
            return
        
        # Manual verification of the spectrum with noise source on
        self.set_noise_source(2)
        user_input = input(f"Is the spectrum correct for noise source=2? (Y/N): ").strip().upper()
        if user_input != "Y":
            logger.info(f"Result not accepted. SAT failed for band {band}.")
            return
        
        self.set_noise_source(0)
        sleep(5)
        logger.info("Setting attenuation levels to new values.")
        self.set_attenuation_levels(self.new_attenuation_levels)
        logger.info(f"Current attenuation levels: {self.get_attenuation_levels()}")

        # Manual verification of the spectrum after attenuation increase and noise source off
        user_input = input(f"Is the spectrum correct for the following attenuation levels: {self.get_attenuation_levels()} (Y/N): ").strip().upper()
        if user_input != "Y":
            logger.info(f"Result not accepted. SAT failed for band {band}.")
            return
        
        logger.info(f"SAT passed for band {band}.")

        # captures = self.capture_packets()
        # print(captures)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the SPFRx SAT flow.")
    parser.add_argument(
        "--tango-host",
        default=os.environ.get("TANGO_HOST"),
        help="Tango host, e.g. tango-databaseds...:10000",
        type=str,
        required=False
    )
    parser.add_argument(
        "--dish-id",
        default=os.environ.get("DISH_ID"),
        help="Dish identifier, e.g. SKA100",
        type=str,
        required=True
    )
    parser.add_argument(
        "--band",
        type=int,
        nargs="*",
        default=[1, 2],
        help="Band(s) to execute. Defaults to both 1 and 2.",
    )
    parser.add_argument(
        "--sat-environment",
        default=os.environ.get("SAT_ENVIRONMENT"),
        help="SAT environment, Choose between 'ITF' or 'Production'",
    )
    parser.add_argument(
        "--spfrx-ip",
        default=os.environ.get("SPFRX_IP"),
        help="SPFRx IP address, e.g. 10.160.1.5",
        type=str,
        required=False
    )
    args = parser.parse_args()
    
    spfrx_sat_executor = SPFRxSATExecutor(
        tango_host=args.tango_host,
        sat_environment=args.sat_environment,
        dish_id=args.dish_id,
        spfrx_ip=args.spfrx_ip
    )
    logger.info("Starting SPFRx SAT execution...")

    if not spfrx_sat_executor.start_plotter():
        raise RuntimeError("Failed to start the plotter. Check plotter logs for more details.")

    for band in [1, 2]:
        logger.info(f"Executing SAT flow for band {band}")
        spfrx_sat_executor.execute(band=band)

    spfrx_sat_executor.stop_plotter()
    

