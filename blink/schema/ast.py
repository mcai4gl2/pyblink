"""AST structures for Blink schema parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .model import QName


@dataclass(frozen=True, slots=True)
class AnnotationAst:
    name: QName
    value: str


@dataclass(frozen=True, slots=True)
class PrimitiveTypeRef:
    name: str


@dataclass(frozen=True, slots=True)
class BinaryTypeRef:
    kind: str
    size: int | None = None


@dataclass(frozen=True, slots=True)
class SequenceTypeRef:
    element_type: "TypeRefAst"


@dataclass(frozen=True, slots=True)
class ObjectTypeRef:
    pass


@dataclass(frozen=True, slots=True)
class NamedTypeRef:
    name: QName
    group_mode: str | None = None


TypeRefAst = PrimitiveTypeRef | BinaryTypeRef | SequenceTypeRef | ObjectTypeRef | NamedTypeRef


@dataclass(frozen=True, slots=True)
class FieldAst:
    name: str
    type_ref: TypeRefAst
    optional: bool = False
    annotations: Sequence[AnnotationAst] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class GroupDefAst:
    name: QName
    type_id: int | None
    fields: Sequence[FieldAst]
    super_name: QName | None = None
    annotations: Sequence[AnnotationAst] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class EnumSymbolAst:
    name: str
    value: int
    annotations: Sequence[AnnotationAst] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class EnumDefAst:
    name: QName
    symbols: Sequence[EnumSymbolAst]
    annotations: Sequence[AnnotationAst] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class TypeDefAst:
    name: QName
    type_ref: TypeRefAst
    annotations: Sequence[AnnotationAst] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SchemaAst:
    namespace: str | None
    enums: Sequence[EnumDefAst] = field(default_factory=tuple)
    type_defs: Sequence[TypeDefAst] = field(default_factory=tuple)
    groups: Sequence[GroupDefAst] = field(default_factory=tuple)
    schema_annotations: Sequence[AnnotationAst] = field(default_factory=tuple)
    incremental_annotations: Sequence["IncrementalAnnotationAst"] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ComponentRefAst:
    name: QName
    member: str | None = None


@dataclass(frozen=True, slots=True)
class IncrementalAnnotationAst:
    target: ComponentRefAst
    annotations: Sequence[AnnotationAst]


__all__ = [
    "AnnotationAst",
    "BinaryTypeRef",
    "ComponentRefAst",
    "EnumDefAst",
    "EnumSymbolAst",
    "FieldAst",
    "GroupDefAst",
    "IncrementalAnnotationAst",
    "NamedTypeRef",
    "ObjectTypeRef",
    "PrimitiveTypeRef",
    "SchemaAst",
    "SequenceTypeRef",
    "TypeDefAst",
    "TypeRefAst",
]
