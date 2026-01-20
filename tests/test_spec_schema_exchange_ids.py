"""Spec-driven tests for schema exchange type identifiers."""

from pathlib import Path

from blink.schema.compiler import compile_schema_file
from blink.schema.model import QName


def test_schema_exchange_ids_match_pdf_spec():
    root = Path(__file__).resolve().parents[1]
    schema = compile_schema_file(root / "schema" / "blink.blink")

    assert schema.get_group(QName("Blink", "GroupDecl")).type_id == 16000
    assert schema.get_group(QName("Blink", "GroupDef")).type_id == 16001
    assert schema.get_group(QName("Blink", "Define")).type_id == 16002
    assert schema.get_group(QName("Blink", "Ref")).type_id == 16003
    assert schema.get_group(QName("Blink", "DynRef")).type_id == 16004
    assert schema.get_group(QName("Blink", "Sequence")).type_id == 16005
    assert schema.get_group(QName("Blink", "String")).type_id == 16006
    assert schema.get_group(QName("Blink", "Binary")).type_id == 16007
    assert schema.get_group(QName("Blink", "Fixed")).type_id == 16008
    assert schema.get_group(QName("Blink", "Enum")).type_id == 16009
    assert schema.get_group(QName("Blink", "SchemaAnnotation")).type_id == 16027


def test_schema_exchange_groups_without_ids():
    root = Path(__file__).resolve().parents[1]
    schema = compile_schema_file(root / "schema" / "blink.blink")

    assert schema.get_group(QName("Blink", "FieldDef")).type_id is None
    assert schema.get_group(QName("Blink", "TypeDef")).type_id is None
    assert schema.get_group(QName("Blink", "Symbol")).type_id is None
    assert schema.get_group(QName("Blink", "Annotated")).type_id is None
    assert schema.get_group(QName("Blink", "Annotation")).type_id is None
    assert schema.get_group(QName("Blink", "NsName")).type_id is None
