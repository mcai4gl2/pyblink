"""Tests for the schema resolver."""

import pytest

from blink.runtime.errors import SchemaError
from blink.schema.ast import (
    AnnotationAst,
    BinaryTypeRef,
    EnumDefAst,
    EnumSymbolAst,
    FieldAst,
    GroupDefAst,
    NamedTypeRef,
    PrimitiveTypeRef,
    SchemaAst,
    SequenceTypeRef,
    TypeDefAst,
)
from blink.schema.model import DynamicGroupRef, EnumType, PrimitiveKind, PrimitiveType, QName, SequenceType, StaticGroupRef
from blink.schema.resolve import resolve_schema


def test_schema_resolver_builds_groups_and_inheritance():
    schema_ast = SchemaAst(
        namespace="Acme",
        enums=(
            EnumDefAst(
                name=QName(None, "Color"),
                symbols=(
                    EnumSymbolAst(name="RED", value=1),
                    EnumSymbolAst(name="GREEN", value=2),
                ),
            ),
        ),
        groups=(
            GroupDefAst(
                name=QName(None, "StaticInfo"),
                type_id=None,
                fields=(FieldAst(name="manufacturer", type_ref=BinaryTypeRef(kind="string")),),
            ),
            GroupDefAst(
                name=QName(None, "Base"),
                type_id=1,
                fields=(
                    FieldAst(
                        name="id",
                        type_ref=PrimitiveTypeRef("u32"),
                        annotations=(AnnotationAst(name=QName(None, "doc"), value="primary"),),
                    ),
                    FieldAst(
                        name="color",
                        type_ref=NamedTypeRef(name=QName(None, "Color")),
                    ),
                ),
            ),
            GroupDefAst(
                name=QName(None, "Order"),
                type_id=2,
                super_name=QName(None, "Base"),
                fields=(
                    FieldAst(
                        name="notes",
                        type_ref=SequenceTypeRef(BinaryTypeRef(kind="string")),
                        optional=True,
                    ),
                    FieldAst(
                        name="extra",
                        type_ref=NamedTypeRef(name=QName(None, "StaticInfo")),
                    ),
                ),
                annotations=(AnnotationAst(name=QName(None, "doc"), value="orders"),),
            ),
        ),
    )

    schema = resolve_schema(schema_ast)

    order_group = schema.get_group(QName("Acme", "Order"))
    assert order_group.super_group is schema.get_group(QName("Acme", "Base"))
    assert order_group.annotations[QName("Acme", "doc")] == "orders"

    fields = list(order_group.all_fields())
    assert [field.name for field in fields] == ["id", "color", "notes", "extra"]

    id_field = fields[0]
    assert id_field.annotations[QName("Acme", "doc")] == "primary"

    color_field = fields[1]
    assert isinstance(color_field.type_ref, EnumType)

    notes_field = fields[2]
    assert notes_field.optional is True
    assert isinstance(notes_field.type_ref, SequenceType)

    extra_field = fields[3]
    assert isinstance(extra_field.type_ref, StaticGroupRef)

    derived = schema.get_group_by_id(2)
    assert derived is order_group


def test_schema_resolver_rejects_nested_sequences():
    schema_ast = SchemaAst(
        namespace=None,
        groups=(
            GroupDefAst(
                name=QName(None, "Bad"),
                type_id=1,
                fields=(
                    FieldAst(
                        name="invalid",
                        type_ref=SequenceTypeRef(
                            SequenceTypeRef(PrimitiveTypeRef("u8"))
                        ),
                    ),
                ),
            ),
        ),
    )

    with pytest.raises(SchemaError):
        resolve_schema(schema_ast)


def test_schema_resolver_unknown_named_type_raises():
    schema_ast = SchemaAst(
        namespace=None,
        groups=(
            GroupDefAst(
                name=QName(None, "Holder"),
                type_id=1,
                fields=(
                    FieldAst(
                        name="missing",
                        type_ref=NamedTypeRef(name=QName(None, "Missing")),
                    ),
                ),
            ),
        ),
    )

    with pytest.raises(SchemaError):
        resolve_schema(schema_ast)


def test_schema_resolver_allows_dynamic_reference_without_type_id():
    schema_ast = SchemaAst(
        namespace=None,
        groups=(
            GroupDefAst(
                name=QName(None, "StaticInfo"),
                type_id=None,
                fields=(FieldAst(name="value", type_ref=PrimitiveTypeRef("u8")),),
            ),
            GroupDefAst(
                name=QName(None, "Holder"),
                type_id=2,
                fields=(
                    FieldAst(
                        name="bad_dynamic",
                        type_ref=NamedTypeRef(
                            name=QName(None, "StaticInfo"), group_mode="dynamic"
                        ),
                    ),
                ),
            ),
        ),
    )

    schema = resolve_schema(schema_ast)
    holder = schema.get_group(QName(None, "Holder"))
    assert isinstance(holder.fields[0].type_ref, DynamicGroupRef)


def test_schema_resolver_supports_type_definitions():
    schema_ast = SchemaAst(
        namespace="Test",
        type_defs=(
            TypeDefAst(
                name=QName(None, "Price"),
                type_ref=PrimitiveTypeRef("decimal"),
            ),
        ),
        groups=(
            GroupDefAst(
                name=QName(None, "Quote"),
                type_id=1,
                fields=(
                    FieldAst(
                        name="px",
                        type_ref=NamedTypeRef(name=QName(None, "Price")),
                    ),
                ),
            ),
        ),
    )

    schema = resolve_schema(schema_ast)
    group = schema.get_group(QName("Test", "Quote"))
    field = next(iter(group.fields))
    assert isinstance(field.type_ref, PrimitiveType)
    assert field.type_ref.primitive == PrimitiveKind.DECIMAL
