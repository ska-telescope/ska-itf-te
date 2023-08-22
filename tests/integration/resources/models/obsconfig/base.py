"""."""
import json
import logging
from datetime import datetime
from typing import Any, Callable, Generic, Literal, NamedTuple, ParamSpec, TypeVar

from ska_tmc_cdm.schemas import CODEC


ReceptorName = Literal[
    "SKA001",
    "SKA002",
    "SKA003",
    "SKA004",
    "SKA005",
    "SKA006",
    "SKA007",
    "SKA008",
    "SKA009",
]

MeerkatDishHame = Literal["MKT000", "MKT001", "MKT002", "MKT003"]

DishName = ReceptorName | MeerkatDishHame


class SB(NamedTuple):
    """."""

    sbi: str
    eb: str
    pb: str


def _load_next_sb():
    date = datetime.now()
    unique = (
        f"{date.year}{date.month:02}{date.day:02}" "-" f"{str(int(date.timestamp()*100))[-5:]}"
    )
    sbi = f"sbi-mvp01-{unique}"
    pb = f"pb-mvp01-{unique}"
    eb = f"eb-mvp01-{unique}"
    return SB(sbi, eb, pb)


class SchedulingBlock:
    """."""

    _sb_initialized = False

    def __init__(self) -> None:
        """_summary_."""
        if not self._sb_initialized:
            logging.info("initialising scheduling block")
            sbi_id, eb_id, pb_id = _load_next_sb()
            self.sbi_id = sbi_id
            self.eb_id = eb_id
            self.pb_id = pb_id
            self._sb_initialized = True

    def load_next_sb(self):
        """."""
        sbi_id, eb_id, pb_id = _load_next_sb()
        self.sbi_id = sbi_id
        self.eb_id = eb_id
        self.pb_id = pb_id


T = TypeVar("T")
P = ParamSpec("P")


class EncodedObject(Generic[T]):
    """."""

    def __init__(self, object_to_encode: T):
        """_summary_.

        :param object_to_encode: _description_
        :type object_to_encode: T
        """
        self._object_to_encode = object_to_encode

    @property
    def as_json(self) -> str:
        """_summary_.

        :return: _description_
        :rtype: str
        """
        if isinstance(self._object_to_encode, dict):
            return json.dumps(self._object_to_encode)
        return CODEC.dumps(self._object_to_encode)

    @property
    def as_dict(self) -> dict[Any, Any]:
        """_summary_.

        :return: _description_
        :rtype: dict[Any, Any]
        """
        return json.loads(self.as_json)

    @property
    def as_object(self) -> T:
        """_summary_.

        :return: _description_
        :rtype: T
        """
        return self._object_to_encode


def encoded(func: Callable[P, T]) -> Callable[P, EncodedObject[T]]:
    """_summary_.

    :param func: _description_
    :type func: Callable[P, T]
    :return: _description_
    :rtype: Callable[P, EncodedObject[T]]
    """

    def inner(*args: P.args, **kwargs: P.kwargs):
        return EncodedObject(func(*args, **kwargs))

    return inner
