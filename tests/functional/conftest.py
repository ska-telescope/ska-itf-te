"""This module contains functional test harness and pytest configuration."""
import os
import threading
from contextlib import contextmanager
from typing import (
    Any,
    Callable,
    ContextManager,
    Dict,
    Generator,
    Iterator,
    Optional,
    Union,
    cast,
    get_args,
)

import pytest
import tango
from ska_control_model import LoggingLevel
from ska_ser_test_equipment.scpi import SupportedProtocol
from ska_ser_test_equipment.signal_generator import (
    SignalGeneratorDevice,
    SignalGeneratorSimulator,
)
from ska_ser_test_equipment.spectrum_analyser import (
    SpectrumAnalyserDevice,
    SpectrumAnalyserSimulator,
)
from ska_tango_testing.context import (
    TangoContextProtocol,
    ThreadedTestTangoContextManager,
    TrueTangoContextManager,
)
from ska_tango_testing.mock.tango import MockTangoEventCallbackGroup

from ska_sky_simulator_controller.sky_sim_ctl_device import (
    SkySimulatorControllerDevice,
)
from ska_sky_simulator_controller.sky_sim_ctl_simulator import (
    SkySimulatorControllerSimulator,
)
from tests.conftest import InstrumentInfoType


# TODO: https://github.com/pytest-dev/pytest-forked/issues/67
# We're stuck on pytest 6.2 until this gets fixed, and this version of
# pytest is not fully typehinted
def pytest_addoption(parser) -> None:  # type: ignore[no-untyped-def]
    """
    Add a command line option to pytest.

    This is a pytest hook, here implemented to add the `--true-context`
    option, used to indicate that a true Tango subsystem is available,
    so there is no need for the test harness to spin up a Tango test
    context.

    :param parser: the command line options parser
    """
    parser.addoption(
        "--true-context",
        action="store_true",
        default=False,
        help=(
            "Tell pytest that you have a true Tango context and don't "
            "need to spin up a Tango test context"
        ),
    )


def pytest_bdd_apply_tag(
    tag: str,
    function: pytest.Function,
) -> Optional[bool]:
    """
    Override how pytest_bdd maps feature file tags to pytest marks.

    :param tag: the tag in the feature file.
    :param function: the python function that pytest_bdd associates the
        tag with

    :return: whether this hook has handled the tag.
    """
    if tag.startswith("XTP-"):
        marker = pytest.mark.xray(tag)
        marker(function)
        return True

    # Fall back to pytest-bdd's default handler
    return None


@pytest.fixture(name="signal_generator_model", scope="session")
def signal_generator_model_fixture() -> str:
    """
    Return the signal generator model.

    :return: the signal generator model.
    """
    return "TSG4104A"


@pytest.fixture(name="signal_generator_initial_values", scope="session")
def signal_generator_initial_values_fixture(
    signal_generator_model: str,
) -> Dict[str, Any]:
    """
    Return a dictionary of expected signal generator device attribute values.

    :param signal_generator_model: name of the model of the signal generator

    :return: expected signal generator device attribute values.
    """
    identities = {
        "TSG4104A": "Tektronix,TSG4104A,s/nC010133,ver2.03.26",
        "SMB100A": "Rohde&Schwarz,SMB100A,1406.6000k03/183286,4.20.028.58",
    }

    initial_values = SignalGeneratorSimulator.DEFAULTS.copy()
    initial_values["identity"] = identities[signal_generator_model]
    initial_values["power_cycled"] = True
    return initial_values


@pytest.fixture(name="signal_generator_simulator_launcher", scope="session")
def signal_generator_simulator_launcher_fixture(
    signal_generator_model: str,
) -> Callable[[], ContextManager[SignalGeneratorSimulator]]:
    """
    Return a context manager factory for a signal generator simulator.

    That is, a callable that, when called, returns a context manager
    that spins up a simulator, yields it for use in testing, and then
    shuts its down afterwards.

    :param signal_generator_model: name of the signal generator model

    :return: a signal generator simulator context manager factory
    """

    @contextmanager
    def launch_simulator() -> Iterator[SignalGeneratorSimulator]:
        address = ("localhost", 0)  # let the kernel give us a port
        server = SignalGeneratorSimulator(
            address, signal_generator_model, power_cycled=True
        )
        with server:
            server_thread = threading.Thread(
                name="Signal generator simulator thread",
                target=server.serve_forever,
            )
            server_thread.daemon = True  # don't hang on exit
            server_thread.start()
            yield server
            server.shutdown()
            server_thread.join()

    return launch_simulator


@pytest.fixture(name="signal_generator_info", scope="session")
def signal_generator_info_fixture(
    signal_generator_model: str,
    signal_generator_simulator_launcher: Callable[
        [], ContextManager[SignalGeneratorSimulator]
    ],
) -> Generator[Dict[str, Any], None, None]:
    """
    Return information about the signal generator.

    The information consists of the protocol, host and port, and whether
    it is a simulator.

    :param signal_generator_model: name of the signal generator model
    :param signal_generator_simulator_launcher: callable that, when
        called, returns a signal generator simulator context that
        yields a simulator that is running as a TCP server.

    :yields: the protocol, host and port of the signal generator
    """
    address_var = f"{signal_generator_model}_ADDRESS"
    if address_var in os.environ:
        [protocol, host, port_str] = os.environ[address_var].split(":")

        assert protocol in get_args(SupportedProtocol)
        yield {
            "protocol": cast(SupportedProtocol, protocol),
            "host": host,
            "port": int(port_str),
            "simulator": False,
        }
    else:
        with signal_generator_simulator_launcher() as simulator:
            host, port = simulator.server_address
            yield {
                "protocol": "tcp",
                "host": host,
                "port": port,
                "simulator": True,
            }


@pytest.fixture(name="spectrum_analyser_model", scope="session")
def spectrum_analyser_model_fixture() -> str:
    """
    Return the spectrum analyser model.

    :return: the spectrum analyser model.
    """
    return "SPECMON26B"


@pytest.fixture(name="signal_generator_initial_values", scope="session")
def spectrum_analyser_initial_values_fixture(
    spectrum_analyser_model: str,
) -> Dict[str, Any]:
    """
    Return a dictionary of expected spectrum analyser device attribute values.

    :param spectrum_analyser_model: name of the model of the spectrum analyser

    :return: expected spectrum analyser device attribute values.
    """
    identities = {
        "SPECMON26B": "TEKTRONIX,SPECMON26B,PQ00112, FV:3.9.0031.0",
    }

    initial_values = SpectrumAnalyserSimulator.DEFAULTS.copy()
    initial_values["identity"] = identities[spectrum_analyser_model]
    return initial_values


@pytest.fixture(name="spectrum_analyser_simulator_launcher", scope="session")
def spectrum_analyser_simulator_launcher_fixture(
    spectrum_analyser_model: str,
) -> Callable[[], ContextManager[SpectrumAnalyserSimulator]]:
    """
    Return a context manager factory for a spectrum analyser simulator.

    That is, a callable that, when called, returns a context manager
    that spins up a simulator, yields it for use in testing, and then
    shuts its down afterwards.

    :param spectrum_analyser_model: name of the spectrum analyser model

    :return: a spectrum analyser simulator context manager factory
    """

    @contextmanager
    def launch_simulator() -> Iterator[SpectrumAnalyserSimulator]:
        address = ("localhost", 0)  # let the kernel give us a port
        server = SpectrumAnalyserSimulator(address, spectrum_analyser_model)
        with server:
            server_thread = threading.Thread(
                name="Spectrum analyser simulator thread",
                target=server.serve_forever,
            )
            server_thread.daemon = True  # don't hang on exit
            server_thread.start()
            yield server
            server.shutdown()
            server_thread.join()

    return launch_simulator


@pytest.fixture(name="spectrum_analyser_info", scope="session")
def spectrum_analyser_info_fixture(
    spectrum_analyser_model: str,
    spectrum_analyser_simulator_launcher: Callable[
        [], ContextManager[SpectrumAnalyserSimulator]
    ],
) -> Generator[InstrumentInfoType, None, None]:
    """
    Return information about the spectrum analyser.

    The information consists of the protocol, host and port, and whether
    it is a simulator.

    :param spectrum_analyser_model: name of the spectrum analyser model
    :param spectrum_analyser_simulator_launcher: callable that, when
        called, returns a spectrum analyser simulator context that
        yields a simulator that is running as a TCP server.

    :yields: the protocol, host and port of the spectrum analyser
    """
    address_var = f"{spectrum_analyser_model}_ADDRESS"
    if address_var in os.environ:
        [protocol, host, port_str] = os.environ[address_var].split(":")

        assert protocol in get_args(SupportedProtocol)
        yield {
            "protocol": cast(SupportedProtocol, protocol),
            "host": host,
            "port": int(port_str),
            "simulator": False,
        }
    else:
        with spectrum_analyser_simulator_launcher() as simulator:
            host, port = simulator.server_address
            yield {
                "protocol": "tcp",
                "host": host,
                "port": port,
                "simulator": True,
            }


@pytest.fixture(name="true_context", scope="session")
def true_context_fixture(request: pytest.FixtureRequest) -> bool:
    """
    Return whether to test against an existing Tango deployment.

    If True, then Tango is already deployed, and the tests will be run
    against that deployment.

    If False, then Tango is not deployed, so the test harness will stand
    up a test context and run the tests against that.

    :param request: A pytest object giving access to the requesting test
        context.

    :return: whether to test against an existing Tango deployment
    """
    if request.config.getoption("--true-context"):
        return True
    if os.getenv("TRUE_TANGO_CONTEXT", None):
        return True
    return False


@pytest.fixture(scope="session")
def deployment_has_simulators(
    signal_generator_info: InstrumentInfoType,
    spectrum_analyser_info: InstrumentInfoType,
) -> bool:
    """
    Return whether this test deployment has any simulators in it.

    Some BDD test steps can only be run against real hardware; this
    fixture tells those steps whether or not to run.

    :param signal_generator_info: information about the signal
        generator, such as the protocol, host and port, and whether it
        is a simulator.
    :param spectrum_analyser_info: information about the spectrum
        analyser, such as the protocol, host and port, and whether it
        is a simulator.

    :return: whether this test deployment has any simulators in it.
    """
    return (
        signal_generator_info["simulator"]
        or spectrum_analyser_info["simulator"]
    )


@pytest.fixture(name="tango_context", scope="session")
def tango_context_fixture(
    true_context: bool,
    signal_generator_model: str,
    signal_generator_info: InstrumentInfoType,
    spectrum_analyser_model: str,
    spectrum_analyser_info: InstrumentInfoType,
) -> Generator[TangoContextProtocol, None, None]:
    """
    Yield a Tango context containing the devices under test.

    :param true_context: whether to test against an existing Tango
        deployment
    :param signal_generator_model: name of the model of the signal generator
    :param signal_generator_info: information about the signal
        generator, such as the protocol, host and port, and whether it
        is a simulator.
    :param spectrum_analyser_model: name of the model of the signal generator
    :param spectrum_analyser_info: information about the spectrum
        analyser, such as the protocol, host and port, and whether it
        is a simulator.

    :yields: a Tango context containing the devices under test
    """
    context_manager: Union[
        TrueTangoContextManager, ThreadedTestTangoContextManager
    ]  # for the type checker
    if true_context:
        context_manager = TrueTangoContextManager()
    else:
        context_manager = ThreadedTestTangoContextManager()
        cast(ThreadedTestTangoContextManager, context_manager).add_device(
            "test-itf/siggen/1",
            SignalGeneratorDevice,
            Model=signal_generator_model,
            Protocol=signal_generator_info["protocol"],
            Host=signal_generator_info["host"],
            Port=signal_generator_info["port"],
            UpdateRate=1.0,
            LoggingLevelDefault=int(LoggingLevel.DEBUG),
        )
        cast(ThreadedTestTangoContextManager, context_manager).add_device(
            "test-itf/spectana/1",
            SpectrumAnalyserDevice,
            Model=spectrum_analyser_model,
            Protocol=spectrum_analyser_info["protocol"],
            Host=spectrum_analyser_info["host"],
            Port=spectrum_analyser_info["port"],
            UpdateRate=1.0,
            LoggingLevelDefault=int(LoggingLevel.DEBUG),
        )
    with context_manager as context:
        yield context


@pytest.fixture(scope="session")
def signal_generator_device(
    tango_context: TangoContextProtocol,
) -> tango.DeviceProxy:
    """
    Return a proxy to the spectrum analyser device.

    :param tango_context: the context in which the device is running.

    :return: a proxy to the signal generator device.
    """
    return tango_context.get_device("test-itf/siggen/1")


@pytest.fixture(scope="session")
def spectrum_analyser_device(
    tango_context: TangoContextProtocol,
) -> tango.DeviceProxy:
    """
    Return a proxy to the spectrum analyser device.

    :param tango_context: the context in which the device is running.

    :return: a proxy to the spectrum analyser device.
    """
    return tango_context.get_device("test-itf/spectana/1")


@pytest.fixture(scope="session")
def change_event_callbacks() -> MockTangoEventCallbackGroup:
    """
    Return a dictionary of change event callbacks with asynchrony support.

    :return: a collections.defaultdict that returns change event
        callbacks by name.
    """
    return MockTangoEventCallbackGroup(
        "siggen_adminMode",
        "siggen_state",
        "siggen_identity",
        "siggen_frequency",
        "siggen_power_dbm",
        "siggen_rf_output_on",
        "siggen_query_error",
        "siggen_device_error",
        "siggen_execution_error",
        "siggen_command_error",
        "siggen_power_cycled",
        "spectana_adminMode",
        "spectana_state",
        "spectana_frequency_peak",
        "spectana_power_peak",
        "spectana_frequency_start",
        "spectana_frequency_stop",
        timeout=10.0,
    )
