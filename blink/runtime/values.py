"""Runtime value helpers used by codecs and schema-aware logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Sequence

from ..schema.model import QName


@dataclass(frozen=True, slots=True)
class DecimalValue:
    """Represents the pair of exponent/mantissa for Blink decimals."""

    exponent: int
    mantissa: int

    def __post_init__(self) -> None:
        if not isinstance(self.exponent, int):
            raise TypeError("DecimalValue.exponent must be int")
        if not isinstance(self.mantissa, int):
            raise TypeError("DecimalValue.mantissa must be int")


@dataclass(slots=True)
class StaticGroupValue:
    """
    Represents the concrete values of a static group.

    Static groups behave similarly to structs – they inline their fields
    instead of introducing a nested message frame.
    """

    fields: Dict[str, Any]

    def __post_init__(self) -> None:
        self.fields = dict(self.fields)

    def __getitem__(self, field_name: str) -> Any:
        return self.fields[field_name]

    def get(self, field_name: str, default: Any = None) -> Any:
        return self.fields.get(field_name, default)

    def items(self):
        return self.fields.items()


@dataclass(slots=True)
class Message:
    """
    Runtime representation of a Blink dynamic group (message).

    Attributes:
        type_name: Qualified name of the schema group backing the message.
        fields: Mapping of field name to decoded value.
        extensions: Optional list of extension messages.
    """

    type_name: QName
    fields: MutableMapping[str, Any] = field(default_factory=dict)
    extensions: Sequence["Message"] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.type_name, QName):
            raise TypeError("type_name must be a QName instance")
        self.fields = dict(self.fields)
        self.extensions = tuple(self.extensions)

    def __getitem__(self, field_name: str) -> Any:
        return self.fields[field_name]

    def get(self, field_name: str, default: Any = None) -> Any:
        return self.fields.get(field_name, default)

    def iter_extensions(self) -> Iterable["Message"]:
        return iter(self.extensions)


__all__ = ["DecimalValue", "Message", "StaticGroupValue"]
