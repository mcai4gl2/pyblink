"""Schema registry to resolve type identifiers during encoding/decoding."""

from __future__ import annotations

from typing import Dict, Iterable, Mapping, MutableMapping

from ..schema.model import GroupDef, QName, Schema
from .errors import RegistryError


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


__all__ = ["TypeRegistry"]
