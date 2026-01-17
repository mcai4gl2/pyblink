"""XML Mapping codec for Blink protocol (Section 8).

The XML format maps Blink messages to XML elements with the following rules:
- Base element <ns:Type> with child elements per field
- Extensions live under <blink:extension> containing nested message elements
- Binary fields default to text for UTF-8, otherwise <field binary="yes">deadbeef</field>
- Namespace URI equals Blink namespace literal
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Dict, List

from ..runtime.errors import DecodeError, EncodeError
from ..runtime.registry import TypeRegistry
from ..runtime.values import DecimalValue, Message, StaticGroupValue
from ..schema.model import (
    BinaryType,
    DynamicGroupRef,
    EnumType,
    ObjectType,
    PrimitiveKind,
    PrimitiveType,
    QName,
    SequenceType,
    StaticGroupRef,
    TypeRef,
)

BLINK_NAMESPACE = "http://blinkprotocol.org/beta4"


def _format_value(value: any, type_ref: TypeRef, registry: TypeRegistry, default_namespace: str | None) -> str:
    """Format a value as XML element text."""
    if value is None:
        raise EncodeError("Cannot format None value in XML format")

    if isinstance(type_ref, PrimitiveType):
        if type_ref.primitive == PrimitiveKind.BOOL:
            return "true" if value else "false"
        if type_ref.primitive == PrimitiveKind.DECIMAL:
            if isinstance(value, DecimalValue):
                exponent, mantissa = value.exponent, value.mantissa
            elif isinstance(value, tuple):
                exponent, mantissa = value
            else:
                raise EncodeError("Decimal values require DecimalValue or tuple")
            return f"{mantissa}e{exponent}"
        return str(int(value))

    if isinstance(type_ref, BinaryType):
        if type_ref.kind == "string":
            return str(value)
        else:
            # Binary data: try UTF-8, otherwise hex string
            data = bytes(value)
            try:
                decoded = data.decode("utf-8")
                # Check if all characters are XML-safe (printable ASCII)
                if all(32 <= ord(c) <= 126 or c in '\n\r\t' for c in decoded):
                    return decoded
            except UnicodeDecodeError:
                pass
            # Fall back to hex
            return data.hex()

    if isinstance(type_ref, EnumType):
        return str(value)

    if isinstance(type_ref, SequenceType):
        raise EncodeError("Sequence values should be handled separately")

    if isinstance(type_ref, StaticGroupRef):
        raise EncodeError("Static group values should be handled separately")

    if isinstance(type_ref, DynamicGroupRef) or isinstance(type_ref, ObjectType):
        raise EncodeError("Dynamic group values should be handled separately")

    raise EncodeError(f"Unsupported type for XML format: {type_ref}")


def _format_message(message: Message, registry: TypeRegistry) -> ET.Element:
    """Format a complete message as XML element."""
    group = registry.get_group_by_name(message.type_name)

    # Create element with namespace
    ns = group.name.namespace or ""
    if ns:
        tag_name = f"{{{ns}}}{group.name.name}"
    else:
        tag_name = group.name.name

    element = ET.Element(tag_name)

    for field in group.all_fields():
        value = message.fields.get(field.name)
        if value is None:
            continue

        if isinstance(field.type_ref, SequenceType):
            # Sequence: create a wrapper element containing multiple child elements
            child = ET.Element(field.name)
            for item in value:
                item_element = ET.Element("item")
                if isinstance(field.type_ref.element_type, (StaticGroupRef, DynamicGroupRef, ObjectType)):
                    # Nested message
                    if isinstance(item, Message):
                        nested = _format_message(item, registry)
                        item_element.append(nested)
                    elif isinstance(item, dict):
                        # Create message from dict
                        type_hint = item.get("$type")
                        if type_hint:
                            qname = QName.parse(str(type_hint), group.name.namespace)
                        else:
                            qname = field.type_ref.element_type.group.name
                        fields = {k: v for k, v in item.items() if k != "$type"}
                        nested_msg = Message(type_name=qname, fields=fields)
                        nested = _format_message(nested_msg, registry)
                        item_element.append(nested)
                else:
                    # Simple value
                    item_element.text = _format_value(item, field.type_ref.element_type, registry, group.name.namespace)
                child.append(item_element)
            element.append(child)
        elif isinstance(field.type_ref, (StaticGroupRef, DynamicGroupRef, ObjectType)):
            # Nested message
            child = ET.Element(field.name)
            if isinstance(value, Message):
                if isinstance(field.type_ref, StaticGroupRef):
                    # For static groups, inline the fields directly
                    for nested_field in value.fields:
                        nested_child = ET.Element(nested_field)
                        nested_child.text = str(value.fields[nested_field])
                        child.append(nested_child)
                else:
                    # For dynamic groups, use nested message element
                    nested = _format_message(value, registry)
                    child.append(nested)
            elif isinstance(value, dict):
                if isinstance(field.type_ref, StaticGroupRef):
                    # For static groups, inline the fields directly
                    for nested_field in value:
                        nested_child = ET.Element(nested_field)
                        nested_child.text = str(value[nested_field])
                        child.append(nested_child)
                else:
                    type_hint = value.get("$type")
                    if type_hint:
                        qname = QName.parse(str(type_hint), group.name.namespace)
                    else:
                        qname = field.type_ref.group.name
                    fields = {k: v for k, v in value.items() if k != "$type"}
                    nested_msg = Message(type_name=qname, fields=fields)
                    nested = _format_message(nested_msg, registry)
                    child.append(nested)
            element.append(child)
        else:
            # Simple value
            child = ET.Element(field.name)
            child.text = _format_value(value, field.type_ref, registry, group.name.namespace)
            # Add binary attribute for non-UTF-8 binary data
            if isinstance(field.type_ref, BinaryType) and field.type_ref.kind != "string":
                data = bytes(value)
                try:
                    data.decode("utf-8")
                except UnicodeDecodeError:
                    child.set("binary", "yes")
            element.append(child)

    # Extensions
    if message.extensions:
        ext_element = ET.Element(f"{{{BLINK_NAMESPACE}}}extension")
        for ext in message.extensions:
            nested = _format_message(ext, registry)
            ext_element.append(nested)
        element.append(ext_element)

    return element


def encode_xml(message: Message, registry: TypeRegistry) -> str:
    """Encode a message to XML string."""
    element = _format_message(message, registry)
    return ET.tostring(element, encoding="unicode")


def _parse_value(element: ET.Element, type_ref: TypeRef, registry: TypeRegistry, default_namespace: str | None, field_name: str | None = None) -> any:
    """Parse a value from XML element."""
    if isinstance(type_ref, PrimitiveType):
        if type_ref.primitive == PrimitiveKind.BOOL:
            text = element.text or ""
            return text.lower() == "true"
        if type_ref.primitive == PrimitiveKind.DECIMAL:
            text = element.text or ""
            # Parse mantissa e exponent format: 15005e-2
            parts = text.split("e")
            if len(parts) != 2:
                raise DecodeError(f"Invalid decimal format: {text}")
            mantissa = int(parts[0])
            exponent = int(parts[1])
            return DecimalValue(exponent=exponent, mantissa=mantissa)
        return int(element.text or "0")

    if isinstance(type_ref, BinaryType):
        text = element.text or ""
        binary_attr = element.get("binary") == "yes"
        if type_ref.kind == "string":
            return text
        else:
            if binary_attr:
                # Hex string
                return bytes.fromhex(text)
            else:
                # Check if text is a valid hex string (even length, only hex digits)
                if len(text) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in text):
                    # It's a hex-encoded string
                    return bytes.fromhex(text)
                # Try UTF-8
                try:
                    return text.encode("utf-8")
                except UnicodeEncodeError:
                    return bytes.fromhex(text)

    if isinstance(type_ref, EnumType):
        return element.text or ""

    if isinstance(type_ref, SequenceType):
        # Sequence: wrapper element containing multiple item elements
        items = []
        for child in element:
            if child.tag == "item":
                items.append(_parse_value(child, type_ref.element_type, registry, default_namespace, None))
        return items

    if isinstance(type_ref, StaticGroupRef):
        # Static group: child elements represent fields
        fields = {}
        for child in element:
            field_def = _find_field(type_ref.group, child.tag)
            if field_def:
                fields[field_def.name] = _parse_value(child, field_def.type_ref, registry, default_namespace, child.tag)
        return StaticGroupValue(fields)

    if isinstance(type_ref, DynamicGroupRef) or isinstance(type_ref, ObjectType):
        # Dynamic group: single child element representing the message
        children = list(element)
        if not children:
            raise DecodeError("Dynamic group element must contain a child message element")
        return _parse_message(children[0], registry, default_namespace or type_ref.group.name.namespace)

    raise DecodeError(f"Unsupported type for XML parsing: {type_ref}")


def _find_field(group: any, name: str) -> any:
    """Find a field definition by tag name."""
    for field in group.all_fields():
        if field.name == name:
            return field
    return None


def _parse_message(element: ET.Element, registry: TypeRegistry, default_namespace: str | None) -> Message:
    """Parse a message from XML element."""
    # Extract namespace and name from element tag
    tag = element.tag
    if tag.startswith("{"):
        # Namespaced element: {namespace}name
        ns, name = tag[1:].split("}", 1)
        qname = QName(ns, name)
    else:
        # Non-namespaced element
        qname = QName(default_namespace, tag)

    group = registry.get_group_by_name(qname)

    fields: Dict[str, any] = {}
    for child in element:
        # Skip extension elements
        if child.tag == f"{{{BLINK_NAMESPACE}}}extension":
            continue

        field_def = _find_field(group, child.tag)
        if field_def:
            fields[field_def.name] = _parse_value(child, field_def.type_ref, registry, group.name.namespace, child.tag)

    extensions: List[Message] = []
    for child in element:
        if child.tag == f"{{{BLINK_NAMESPACE}}}extension":
            for ext_child in child:
                extensions.append(_parse_message(ext_child, registry, group.name.namespace))

    return Message(type_name=qname, fields=fields, extensions=tuple(extensions))


def decode_xml(s: str, registry: TypeRegistry) -> Message:
    """Decode a message from XML string."""
    element = ET.fromstring(s)
    return _parse_message(element, registry, None)


def encode_xml_stream(messages: List[Message], registry: TypeRegistry) -> str:
    """Encode multiple messages to XML (one root element per message)."""
    return "\n".join(encode_xml(msg, registry) for msg in messages)


def decode_xml_stream(s: str, registry: TypeRegistry) -> List[Message]:
    """Decode multiple messages from XML (one root element per line)."""
    messages = []
    for line in s.splitlines():
        line = line.strip()
        if line:
            messages.append(decode_xml(line, registry))
    return messages


__all__ = [
    "encode_xml",
    "decode_xml",
    "encode_xml_stream",
    "decode_xml_stream",
]