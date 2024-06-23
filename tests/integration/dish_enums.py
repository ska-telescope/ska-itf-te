"""tests/integration/dish_enums.py."""

import enum


class DishMode(enum.IntEnum):
    """DishMode enumerations."""

    STARTUP = 0
    SHUTDOWN = 1
    STANDBY_LP = 2
    STANDBY_FP = 3
    MAINTENANCE = 4
    STOW = 5
    CONFIG = 6
    OPERATE = 7
    UNKNOWN = 8


class SPFOperatingMode(enum.IntEnum):
    """SPFOperatingMode  enumerations."""

    UNKNOWN = 0
    STARTUP = 1
    STANDBY_LP = 2
    OPERATE = 3
    MAINTENANCE = 4
    ERROR = 5


class SPFRxOperatingMode(enum.IntEnum):
    """SPFRxOperatingMode enumerations."""

    UNKNOWN = 0
    STARTUP = 1
    STANDBY = 2
    DATA_CAPTURE = 3
    CONFIGURE = 4
    MAINTENANCE = 5


class DSOperatingMode(enum.IntEnum):
    """DSOperatingMode enumerations."""

    UNKNOWN = 0
    STARTUP = 1
    STANDBY_LP = 2
    STANDBY_FP = 3
    MAINTENANCE = 4
    STOW = 5
    ESTOP = 6
    POINT = 7


class PointingState(enum.IntEnum):
    """PointingState enumerations."""

    READY = 0
    SLEW = 1
    TRACK = 2
    SCAN = 3
    UNKNOWN = 4


class Band(enum.IntEnum):
    """Band enumerations."""

    NONE = 0
    B1 = 1
    B2 = 2
    B3 = 3
    B4 = 4
    B5a = 5
    B5b = 6
    UNKNOWN = 7


class IndexerPosition(enum.IntEnum):
    """IndexerPosition enumerations."""

    UNKNOWN = 0
    B1 = 1
    B2 = 2
    B3 = 3
    B4 = 4
    B5 = 5
    MOVING = 6
    ERROR = 7


class BandInFocus(enum.IntEnum):
    """BandInFocus enumerations."""

    UNKNOWN = 0
    B1 = 1
    B2 = 2
    B3 = 3
    B4 = 4
    B5 = 5


class SPFBandInFocus(enum.IntEnum):
    """SPFBandInFocus enumerations."""

    UNKNOWN = 0
    B1 = 1
    B2 = 2
    B3 = 3
    B4 = 4
    B5a = 5
    B5b = 6


class TrackInterpolationMode(enum.IntEnum):
    """TrackInterpolationMode enumerations."""

    NEWTON = 0
    SPLINE = 1


class TrackProgramMode(enum.IntEnum):
    """TrackProgramMode enumerations."""

    TABLEA = 0
    TABLEB = 1
    POLY = 2


class TrackTableLoadMode(enum.IntEnum):
    """TrackTableLoadMode enumerations."""

    NEW = 0
    APPEND = 1
    RESET = 2


class PowerState(enum.IntEnum):
    """PowerState enumerations."""

    UPS = 0
    LOW = 1
    FULL = 2


class SPFPowerState(enum.IntEnum):
    """SPFPowerState enumerations."""

    # enums are from ICD
    UNKNOWN = 0
    LOW_POWER = 1
    FULL_POWER = 2


class DSPowerState(enum.IntEnum):
    """DSPowerState enumerations."""

    # enums are from ICD
    OFF = 0
    UPS = 1
    FULL_POWER = 2
    LOW_POWER = 3
    UNKNOWN = 4


class CapabilityStates(enum.IntEnum):
    """CapabilityStates enumerations."""

    UNAVAILABLE = 0
    STANDBY = 1
    CONFIGURING = 2
    OPERATE_DEGRADED = 3
    OPERATE_FULL = 4
    UNKNOWN = 5


class SPFCapabilityStates(enum.IntEnum):
    """SPFCapabilityStates enumerations."""

    UNAVAILABLE = 0
    STANDBY = 1
    OPERATE_DEGRADED = 2
    OPERATE_FULL = 3


class SPFRxCapabilityStates(enum.IntEnum):
    """SPFRxCapabilityStates enumerations."""

    UNKNOWN = 0
    UNAVAILABLE = 1
    STANDBY = 2
    CONFIGURE = 3
    OPERATE = 4
