"""Schema registry to resolve type identifiers during encoding/decoding."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Mapping, MutableMapping

from ..schema.compiler import compile_schema, compile_schema_file
from ..schema.model import FieldDef, GroupDef, PrimitiveType, PrimitiveKind, QName, Schema, SequenceType, BinaryType, EnumType, SequenceType, StaticGroupRef, DynamicGroupRef, TypeRef, BinaryType, EnumType, StaticGroupRef, DynamicGroupRef, SequenceType
from .errors import RegistryError


class SchemaRegistry:
    """
    Mutable registry that can apply schema transport messages (GroupDecl, GroupDef, etc.)
    and lazily emit TypeRegistry instances for codecs.
    """

    def __init__(self, schema: Schema | None = None) -> None:
        self._schema = schema or Schema(namespace=None)
        self._type_registry = TypeRegistry(self._schema)

    @property
    def schema(self) -> Schema:
        return self._schema

    @property
    def type_registry(self) -> TypeRegistry:
        return self._type_registry

    def apply_group_decl(self, name: Dict[str, str], type_id: int) -> GroupDef:
        qname = QName(namespace=name.get("Ns"), name=name["Name"])
        key = str(qname)
        if key in self._schema.groups:
            group = self._schema.groups[key]
            group.type_id = type_id
        else:
            group = GroupDef(name=qname, type_id=type_id, fields=tuple())
            self._schema.add_group(group)
            self._type_registry.register_group(group)
        return group


class TypeRegistry:
    """
    In-memory registry mapping Blink type IDs and names to group definitions.

    The registry is intentionally lightweight; callers are expected to provide
    synchronisation if they mutate it concurrently.
    """

    def __init__(self, schema: Schema | None = None) -> None:
        self._by_name: Dict[str, GroupDef] = {}
        self._by_id: Dict[int, GroupDef] = {}
        if schema:
            for group in schema.groups.values():
                self.register_group(group)

    def register_group(self, group: GroupDef) -> None:
        key = str(group.name)
        if key in self._by_name:
            raise RegistryError(f"group {key} already registered")
        if group.type_id is not None:
            if group.type_id in self._by_id:
                raise RegistryError(f"type id {group.type_id} already registered")
            self._by_id[group.type_id] = group
        self._by_name[key] = group

    def get_group_by_name(self, qname: QName | str) -> GroupDef:
        key = str(qname)
        try:
            return self._by_name[key]
        except KeyError as exc:
            raise RegistryError(f"unknown group {key}") from exc

    def get_group_by_id(self, type_id: int) -> GroupDef:
        try:
            return self._by_id[type_id]
        except KeyError as exc:
            raise RegistryError(f"unknown type id {type_id}") from exc

    def __contains__(self, qname: QName | str) -> bool:
        try:
            self.get_group_by_name(qname)
            return True
        except RegistryError:
            return False

    def known_type_ids(self) -> Iterable[int]:
        return self._by_id.keys()

    @classmethod
    def from_schema(cls, schema: Schema) -> "TypeRegistry":
        """Create a registry from a resolved ``Schema`` instance."""

        return cls(schema)

    @classmethod
    def from_schema_text(cls, text: str, *, filename: str | None = None) -> "TypeRegistry":
        """Parse + resolve ``text`` and build a registry."""

        schema = compile_schema(text, filename=filename)
        return cls(schema)

    @classmethod
    def from_schema_file(cls, path: str | Path) -> "TypeRegistry":
        """Load a `.blink` schema file and build a registry."""

        schema = compile_schema_file(path)
        return cls(schema)


__all__ = ["SchemaRegistry", "TypeRegistry"]
