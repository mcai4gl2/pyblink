"""Tests for Blink schema parser integration."""

import pytest

from blink.runtime.errors import SchemaError
from pathlib import Path

from blink.schema import compile_schema, compile_schema_file, parse_schema
from blink.schema.model import DynamicGroupRef, ObjectType, PrimitiveKind, PrimitiveType, QName, SequenceType, StaticGroupRef
from blink.schema.resolve import SchemaResolver, resolve_schema
from blink.runtime.registry import TypeRegistry


def test_parse_and_resolve_schema():
    schema_text = """
    namespace Trade

    Price = decimal

    Color = Red | Green | Blue

    Instrument/5 ->
        string Symbol,
        Price Px,
        Color Tone

    Order/7 : Instrument ->
        u64 OrderId,
        Instrument* Parent?,
        Instrument [] Legs,
        object [] Extension?
    """

    schema_ast = parse_schema(schema_text)
    assert schema_ast.namespace == "Trade"
    assert len(schema_ast.enums) == 1
    enum = schema_ast.enums[0]
    assert enum.name == QName(None, "Color")
    assert [symbol.name for symbol in enum.symbols] == ["Red", "Green", "Blue"]
    assert [symbol.value for symbol in enum.symbols] == [0, 1, 2]
    assert len(schema_ast.type_defs) == 1

    schema = resolve_schema(schema_ast)
    instrument = schema.get_group(QName("Trade", "Instrument"))
    order = schema.get_group(QName("Trade", "Order"))

    # Field order includes inherited members.
    field_names = [field.name for field in order.all_fields()]
    assert field_names == ["Symbol", "Px", "Tone", "OrderId", "Parent", "Legs", "Extension"]

    px_field = instrument.fields[1]
    assert isinstance(px_field.type_ref, PrimitiveType)
    assert px_field.type_ref.primitive == PrimitiveKind.DECIMAL

    parent_field = order.fields[1]
    assert isinstance(parent_field.type_ref, DynamicGroupRef)

    legs_field = order.fields[2]
    assert isinstance(legs_field.type_ref, SequenceType)
    assert isinstance(legs_field.type_ref.element_type, StaticGroupRef)

    extension_field = order.fields[3]
    assert isinstance(extension_field.type_ref, SequenceType)
    assert isinstance(extension_field.type_ref.element_type, ObjectType)


def test_incremental_annotations_override_inline_metadata():
    schema_text = """
    namespace Demo

    @doc="inline"
    Msg/1 ->
        string Payload/7?

    Msg <- @doc="incremental"
    Msg.Payload <- @doc="field override"
    schema <- @version="1"
    """
    schema = compile_schema(schema_text)

    msg = schema.get_group(QName("Demo", "Msg"))
    assert msg.annotations[QName("Demo", "doc")] == "incremental"

    payload_field = msg.fields[0]
    assert payload_field.annotations[QName("Demo", "doc")] == "field override"
    assert payload_field.annotations[QName("blink", "id")] == "7"

    assert schema.annotations[QName("Demo", "version")] == "1"


def test_enum_symbol_annotations_and_incremental():
    schema_text = """
    namespace Demo

    @doc="inline-color"
    Color = @doc="red" Red/1 | Blue

    Color.Blue <- @doc="blue override"
    """
    schema_ast = parse_schema(schema_text)
    resolver = SchemaResolver(schema_ast)
    resolver.resolve()
    enum = resolver._ensure_enum("Demo:Color")
    assert enum.annotations[QName("Demo", "doc")] == "inline-color"
    assert enum.symbol_annotations["Red"][QName("Demo", "doc")] == "red"
    assert enum.symbol_annotations["Blue"][QName("Demo", "doc")] == "blue override"


def test_compile_schema_file_real_fixture():
    root = Path(__file__).resolve().parents[1]
    schema_path = root / "schema" / "blink.blink"
    schema = compile_schema_file(schema_path)

    group_decl = schema.get_group(QName("Blink", "GroupDecl"))
    field_names = [field.name for field in group_decl.fields]
    assert field_names == ["Name", "Id"]

    group_def = schema.get_group(QName("Blink", "GroupDef"))
    assert group_def.super_group is not None
    assert group_def.super_group.name.name == "Annotated"

    # Confirm we can resolve a type reference embedded inside a field.
    field_def = next(f for f in group_def.fields if f.name == "Fields")
    assert isinstance(field_def.type_ref, SequenceType)


def test_type_registry_from_schema_file_examples():
    root = Path(__file__).resolve().parents[1]
    registry = TypeRegistry.from_schema_file(
        root / "schema" / "examples" / "trading.blink"
    )
    order = registry.get_group_by_name(QName("Trading", "Order"))
    assert [field.name for field in order.fields[:3]] == ["Instrument", "Price", "Quantity"]
