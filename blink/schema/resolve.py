"""Schema AST resolution into runtime Schema objects."""

from __future__ import annotations

from typing import Dict, Iterable, Mapping, Sequence

from ..runtime.errors import SchemaError
from .ast import (
    AnnotationAst,
    BinaryTypeRef,
    EnumDefAst,
    EnumSymbolAst,
    FieldAst,
    GroupDefAst,
    IncrementalAnnotationAst,
    NamedTypeRef,
    ObjectTypeRef,
    PrimitiveTypeRef,
    SchemaAst,
    SequenceTypeRef,
    TypeDefAst,
    TypeRefAst,
)
from .model import (
    BinaryType,
    DynamicGroupRef,
    EnumType,
    FieldDef,
    GroupDef,
    ObjectType,
    PrimitiveKind,
    PrimitiveType,
    QName,
    Schema,
    SequenceType,
    StaticGroupRef,
    TypeRef,
)


class SchemaResolver:
    """Resolves a ``SchemaAst`` into the runtime ``Schema`` model."""

    def __init__(self, schema_ast: SchemaAst):
        self._schema_ast = schema_ast
        self._schema = Schema(namespace=schema_ast.namespace)
        self._namespace = schema_ast.namespace
        self._enum_asts: Dict[str, EnumDefAst] = {}
        self._enum_cache: Dict[str, EnumType] = {}
        self._enum_names: Dict[str, QName] = {}
        self._group_asts: Dict[str, GroupDefAst] = {}
        self._group_names: Dict[str, QName] = {}
        self._group_cache: Dict[str, GroupDef] = {}
        self._type_defs: Dict[str, TypeDefAst] = {}
        self._type_cache: Dict[str, TypeRef] = {}
        self._incremental_annotations: Dict[str, list[AnnotationAst]] = {}
        self._building: set[str] = set()
        self._resolving_types: set[str] = set()
        self._definitions: set[str] = set()
        self._register_enums(schema_ast.enums)
        self._register_type_defs(schema_ast.type_defs)
        self._register_groups(schema_ast.groups)
        self._index_incremental_annotations(schema_ast.incremental_annotations)
        self._schema.annotations = self._collect_annotations(schema_ast.schema_annotations, "schema")

    def resolve(self) -> Schema:
        """Return the resolved schema."""

        for key in self._group_asts:
            self._ensure_group(key)
        return self._schema

    def _register_enums(self, enums: Sequence[EnumDefAst]) -> None:
        for enum_ast in enums:
            qname = self._qualify_decl_name(enum_ast.name)
            key = str(qname)
            self._ensure_unique_name(key)
            self._enum_asts[key] = enum_ast
            self._enum_names[key] = qname

    def _register_type_defs(self, type_defs: Sequence[TypeDefAst]) -> None:
        for type_def in type_defs:
            qname = self._qualify_decl_name(type_def.name)
            key = str(qname)
            self._ensure_unique_name(key)
            self._type_defs[key] = type_def

    def _register_groups(self, groups: Sequence[GroupDefAst]) -> None:
        for group_ast in groups:
            qname = self._qualify_decl_name(group_ast.name)
            key = str(qname)
            self._ensure_unique_name(key)
            self._group_asts[key] = group_ast
            self._group_names[key] = qname

    def _ensure_unique_name(self, key: str) -> None:
        if key in self._definitions:
            raise SchemaError(f"Duplicate definition for {key}")
        self._definitions.add(key)

    def _qualify_decl_name(self, raw: QName) -> QName:
        namespace = raw.namespace if raw.namespace else self._namespace
        return QName(namespace, raw.name)

    def _candidate_keys(self, raw: QName) -> Iterable[str]:
        if raw.namespace:
            yield str(raw)
            return
        if self._namespace:
            yield f"{self._namespace}:{raw.name}"
        yield raw.name

    def _resolve_name(
        self, raw: QName, population: Mapping[str, object], kind: str
    ) -> str:
        for candidate in self._candidate_keys(raw):
            if candidate in population:
                return candidate
        raise SchemaError(f"Unknown {kind} {raw}")

    def _collect_annotations(
        self, annotations: Sequence[AnnotationAst], extra_key: str | None = None
    ) -> Dict[QName, str]:
        result: Dict[QName, str] = {}
        for annotation in annotations:
            key = self._qualify_decl_name(annotation.name)
            result[key] = annotation.value
        if extra_key:
            for annotation in self._incremental_annotations.get(extra_key, []):
                key = self._qualify_decl_name(annotation.name)
                result[key] = annotation.value
        return result

    def _ensure_group(self, key: str, *, allow_partial: bool = True) -> GroupDef:
        if key in self._group_cache:
            if not allow_partial and key in self._building:
                name = self._group_names[key]
                raise SchemaError(f"Cyclic inheritance involving {name}")
            return self._group_cache[key]
        if key not in self._group_asts:
            raise SchemaError(f"Unknown group {key}")
        ast = self._group_asts[key]
        annotations = self._collect_annotations(ast.annotations, key)
        group = GroupDef(
            name=self._group_names[key],
            type_id=ast.type_id,
            fields=tuple(),
            annotations=annotations,
        )
        self._group_cache[key] = group
        self._building.add(key)
        try:
            group.super_group = self._resolve_super(key, ast)
            group.fields = tuple(self._resolve_fields(key, ast))
        finally:
            self._building.discard(key)
        if str(group.name) not in self._schema.groups:
            self._schema.add_group(group)
        return group

    def _resolve_super(self, group_key: str, ast: GroupDefAst) -> GroupDef | None:
        if ast.super_name is None:
            return None
        super_key = self._resolve_name(ast.super_name, self._group_asts, "group")
        return self._ensure_group(super_key, allow_partial=False)

    def _resolve_fields(self, group_key: str, ast: GroupDefAst) -> Iterable[FieldDef]:
        for field_ast in ast.fields:
            type_ref = self._resolve_type(field_ast.type_ref)
            annotations = self._collect_annotations(
                field_ast.annotations, f"{group_key}.{field_ast.name}"
            )
            yield FieldDef(
                name=field_ast.name,
                type_ref=type_ref,
                optional=field_ast.optional,
                annotations=annotations,
            )

    def _resolve_type(self, type_ref: TypeRefAst, *, in_sequence: bool = False) -> TypeRef:
        if isinstance(type_ref, PrimitiveTypeRef):
            kind = PrimitiveKind.from_name(type_ref.name)
            return PrimitiveType(kind)
        if isinstance(type_ref, BinaryTypeRef):
            if type_ref.kind not in {"string", "binary", "fixed"}:
                raise SchemaError(f"Unknown binary type {type_ref.kind}")
            return BinaryType(type_ref.kind, type_ref.size)
        if isinstance(type_ref, SequenceTypeRef):
            if in_sequence:
                raise SchemaError("Blink does not allow nested sequences")
            element_type = self._resolve_type(type_ref.element_type, in_sequence=True)
            if isinstance(element_type, SequenceType):
                raise SchemaError("Blink does not allow nested sequences")
            return SequenceType(element_type)
        if isinstance(type_ref, ObjectTypeRef):
            return ObjectType()
        if isinstance(type_ref, NamedTypeRef):
            return self._resolve_named_type(type_ref)
        raise SchemaError(f"Unsupported type reference {type_ref!r}")

    def _resolve_named_type(self, ref: NamedTypeRef) -> TypeRef:
        group: GroupDef | None = None
        for candidate in self._candidate_keys(ref.name):
            if candidate in self._enum_asts:
                if ref.group_mode:
                    raise SchemaError(
                        f"Enum {self._enum_names[candidate]} cannot use group mode {ref.group_mode}"
                    )
                return self._ensure_enum(candidate)
            if candidate in self._group_asts:
                group = self._ensure_group(candidate)
                break
            if candidate in self._type_defs:
                return self._ensure_type_def(candidate)
        else:
            raise SchemaError(f"Unknown type {ref.name}")
        assert group is not None
        mode = ref.group_mode
        if mode == "static":
            return StaticGroupRef(group)
        if mode == "dynamic":
            if group.type_id is None:
                # Some schema description documents (like the blink schema transport)
                # omit type ids even though they describe dynamic payloads. We allow
                # such references here and defer strict enforcement to the codec layer.
                return DynamicGroupRef(group)
            return DynamicGroupRef(group)
        # Default to static usage unless explicitly marked as dynamic.
        return StaticGroupRef(group)

    def _ensure_type_def(self, key: str) -> TypeRef:
        if key in self._type_cache:
            return self._type_cache[key]
        if key not in self._type_defs:
            raise SchemaError(f"Unknown type definition {key}")
        if key in self._resolving_types:
            raise SchemaError(f"Cyclic type definition involving {self._type_defs[key].name}")
        self._resolving_types.add(key)
        try:
            resolved = self._resolve_type(self._type_defs[key].type_ref)
        finally:
            self._resolving_types.remove(key)
        self._type_cache[key] = resolved
        return resolved

    def _ensure_enum(self, key: str) -> EnumType:
        if key in self._enum_cache:
            return self._enum_cache[key]
        if key not in self._enum_asts:
            raise SchemaError(f"Unknown enum {key}")
        ast = self._enum_asts[key]
        annotations = self._collect_annotations(ast.annotations, key)
        symbols: Dict[str, int] = {}
        symbol_annotations: Dict[str, Dict[QName, str]] = {}
        for symbol_ast in ast.symbols:
            if symbol_ast.name in symbols:
                raise SchemaError(f"Duplicate enum symbol {symbol_ast.name} in {key}")
            symbols[symbol_ast.name] = symbol_ast.value
            symbol_key = f"{key}.{symbol_ast.name}"
            symbol_annotations[symbol_ast.name] = self._collect_annotations(
                symbol_ast.annotations, symbol_key
            )
        enum = EnumType(
            name=self._enum_names[key],
            symbols=symbols,
            annotations=annotations,
            symbol_annotations=symbol_annotations,
        )
        self._enum_cache[key] = enum
        return enum

    def _index_incremental_annotations(
        self, incremental: Sequence[IncrementalAnnotationAst]
    ) -> None:
        for entry in incremental:
            qname = self._qualify_decl_name(entry.target.name)
            base_key = str(qname)
            member = entry.target.member
            key = base_key
            if member:
                key = f"{base_key}.{member}"
            if member:
                if base_key in self._group_asts:
                    if not any(field.name == member for field in self._group_asts[base_key].fields):
                        raise SchemaError(f"Unknown field {member} on {base_key}")
                elif base_key in self._enum_asts:
                    if not any(symbol.name == member for symbol in self._enum_asts[base_key].symbols):
                        raise SchemaError(f"Unknown enum symbol {member} on {base_key}")
                else:
                    raise SchemaError(f"Unknown component {base_key} for incremental annotation")
            else:
                if base_key not in self._group_asts and base_key not in self._enum_asts and base_key not in self._type_defs:
                    raise SchemaError(f"Unknown component {base_key} for incremental annotation")
            self._incremental_annotations.setdefault(key, []).extend(entry.annotations)


def resolve_schema(schema_ast: SchemaAst) -> Schema:
    """Public helper to resolve ``SchemaAst`` into ``Schema``."""

    resolver = SchemaResolver(schema_ast)
    return resolver.resolve()


__all__ = ["SchemaResolver", "resolve_schema"]
