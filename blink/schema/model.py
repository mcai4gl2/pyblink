"""Schema model primitives shared by parser and runtime registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, Mapping, MutableMapping, Optional, Sequence

from ..runtime.errors import SchemaError


@dataclass(frozen=True, slots=True)
class QName:
    """Represents a qualified Blink name (namespace:name)."""

    namespace: str | None
    name: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("QName.name cannot be empty")

    def __str__(self) -> str:
        return f"{self.namespace}:{self.name}" if self.namespace else self.name

    @classmethod
    def parse(cls, raw: str, default_namespace: str | None = None) -> "QName":
        if ":" in raw:
            namespace, name = raw.split(":", 1)
            namespace = namespace or None
        else:
            namespace, name = default_namespace, raw
        return cls(namespace, name)


class PrimitiveKind(str, Enum):
    U8 = "u8"
    U16 = "u16"
    U32 = "u32"
    U64 = "u64"
    I8 = "i8"
    I16 = "i16"
    I32 = "i32"
    I64 = "i64"
    BOOL = "bool"
    F64 = "f64"
    DECIMAL = "decimal"
    MILLITIME = "millitime"
    NANOTIME = "nanotime"
    DATE = "date"
    TIME_OF_DAY_MILLI = "timeOfDayMilli"
    TIME_OF_DAY_NANO = "timeOfDayNano"

    @classmethod
    def from_name(cls, name: str) -> "PrimitiveKind":
        try:
            return PrimitiveKind(name)
        except ValueError as exc:
            raise SchemaError(f"Unknown primitive type: {name}") from exc


@dataclass(frozen=True, slots=True)
class PrimitiveType:
    primitive: PrimitiveKind


@dataclass(frozen=True, slots=True)
class BinaryType:
    """Represents string, binary, or fixed types."""

    kind: str  # "string", "binary", "fixed"
    size: int | None = None

    def __post_init__(self) -> None:
        if self.kind == "fixed" and (self.size is None or self.size <= 0):
            raise ValueError("fixed type requires a positive size")
        if self.kind != "fixed" and self.size is not None:
            raise ValueError("only fixed type can specify size")


@dataclass(frozen=True, slots=True)
class EnumType:
    name: QName
    symbols: Mapping[str, int]

    def __post_init__(self) -> None:
        values = set()
        for symbol, value in self.symbols.items():
            if value in values:
                raise SchemaError(f"Duplicate enum value {value} for symbol {symbol}")
            values.add(value)

    def to_symbol(self, value: int) -> str:
        for symbol, number in self.symbols.items():
            if number == value:
                return symbol
        raise SchemaError(f"Enum {self.name} has no symbol for value {value}")

    def to_value(self, symbol: str) -> int:
        try:
            return self.symbols[symbol]
        except KeyError as exc:
            raise SchemaError(f"Enum {self.name} has no symbol {symbol}") from exc


@dataclass(frozen=True, slots=True)
class FieldDef:
    name: str
    type_ref: "TypeRef"
    optional: bool = False
    annotations: Mapping[QName, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Field name cannot be empty")


@dataclass(slots=True)
class GroupDef:
    name: QName
    type_id: int | None
    fields: Sequence[FieldDef]
    super_group: "GroupDef | None" = None
    annotations: Mapping[QName, str] = field(default_factory=dict)
    is_dynamic: bool = True

    def all_fields(self) -> Iterable[FieldDef]:
        if self.super_group:
            yield from self.super_group.all_fields()
        yield from self.fields


@dataclass(slots=True)
class Schema:
    namespace: str | None
    groups: Dict[str, GroupDef] = field(default_factory=dict)
    type_ids: Dict[int, GroupDef] = field(default_factory=dict)

    def add_group(self, group: GroupDef) -> None:
        key = str(group.name)
        if key in self.groups:
            raise SchemaError(f"Duplicate group definition for {key}")
        if group.type_id is not None:
            if group.type_id in self.type_ids:
                raise SchemaError(f"Duplicate type id {group.type_id}")
            self.type_ids[group.type_id] = group
        self.groups[key] = group

    def get_group(self, qname: QName) -> GroupDef:
        try:
            return self.groups[str(qname)]
        except KeyError as exc:
            raise SchemaError(f"Unknown group {qname}") from exc

    def get_group_by_id(self, type_id: int) -> GroupDef:
        try:
            return self.type_ids[type_id]
        except KeyError as exc:
            raise SchemaError(f"Unknown type id {type_id}") from exc


@dataclass(frozen=True, slots=True)
class SequenceType:
    element_type: "TypeRef"


@dataclass(frozen=True, slots=True)
class StaticGroupRef:
    group: "GroupDef"


@dataclass(frozen=True, slots=True)
class DynamicGroupRef:
    group: "GroupDef"


TypeRef = PrimitiveType | BinaryType | SequenceType | EnumType | StaticGroupRef | DynamicGroupRef


__all__ = [
    "BinaryType",
    "EnumType",
    "FieldDef",
    "GroupDef",
    "PrimitiveKind",
    "PrimitiveType",
    "QName",
    "Schema",
    "SequenceType",
    "StaticGroupRef",
    "DynamicGroupRef",
]
