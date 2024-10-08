"""Module containing commonly used enums."""

from enum import IntEnum


class DishMode(IntEnum):
    """DishMode enum."""

    STARTUP = 0
    SHUTDOWN = 1
    STANDBY_LP = 2
    STANDBY_FP = 3
    MAINTENANCE = 4
    STOW = 5
    CONFIG = 6
    OPERATE = 7
    UNKNOWN = 8
