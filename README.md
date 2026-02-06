# PyBlink

PyBlink is a Blink protocol implementation in Python, providing schema parsing, multiple codec formats, and dynamic schema exchange capabilities.

## Features

- **Schema Parsing**: Parse Blink schema definitions (`.blink` files) into resolved in-memory schemas
- **Multiple Codecs**:
  - **Compact Binary**: Efficient binary encoding for production use
  - **Native Binary**: Fixed-width binary format optimized for speed
  - **Tag Format**: Human-readable text format with escaping support
  - **JSON Mapping**: JSON representation with numeric thresholds and special float tokens
  - **XML Mapping**: XML representation with Blink namespaces
- **Dynamic Schema Exchange**: Runtime schema updates via reserved type IDs (16000-16383)
- **CLI Tooling**: Command-line utilities for encoding/decoding and schema management
- **Web Playground**: Interactive web application for testing Blink message conversions

## Live Demo

🚀 **Try PyBlink now**: [https://pyblink.pages.dev/](https://pyblink.pages.dev/)

The Blink Message Playground is deployed and ready to use! No installation required - just open the link and start converting messages between all supported formats.

## Quick Start

### Blink Message Playground (Web UI)

The easiest way to explore PyBlink is through the **Blink Message Playground** - a web application that lets you interactively convert messages between all supported formats.

**First-time setup:**

```bash
# Windows - Install all dependencies
setup.bat
```

**Start both servers with one command:**

```bash
# Windows
start.bat

# Cross-platform (using Make)
make start
```

This will start:
- **Backend API** at http://127.0.0.1:8000 (FastAPI with auto-generated docs at `/docs`)
- **Frontend App** at http://localhost:3000 (React + TypeScript)

**Manual startup:**

```bash
# Backend only
make start-backend
# or: cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Frontend only
make start-frontend
# or: cd frontend && npm start
```

**Features:**
- Schema editor with validation
- Input panel supporting all 5 formats (JSON, Tag, XML, Compact Binary, Native Binary)
- Real-time conversion to all output formats
- Binary hex viewer with decoded annotations
- Copy-to-clipboard for all outputs
- Default example demonstrates nested classes and subclasses

See `doc/IMPLEMENTATION.md` for detailed architecture and `doc/QUICKSTART.md` for more information.

### Python Library Usage

For programmatic usage, see the sections below on compiling schemas and using codecs.

## Compiling Schemas

Blink schemas (`.blink` files) can be parsed and resolved in a single call via `blink.schema.compile_schema` or by building a `TypeRegistry` directly. A sample trading schema lives under `schema/examples/trading.blink`.

Example usage:

```python
from blink.schema import compile_schema_file
from blink.runtime.registry import TypeRegistry

schema = compile_schema_file("schema/examples/trading.blink")
registry = TypeRegistry.from_schema(schema)

order = registry.get_group_by_name("Trading:Order")
print("Order fields:", [field.name for field in order.fields])
```

You can also skip the intermediate `Schema` object:

```python
registry = TypeRegistry.from_schema_file("schema/examples/trading.blink")
```

## Codec Usage

### Compact Binary

The `blink.codec.compact` module provides schema-aware `encode_message`/`decode_message` for Compact Binary encoding.

**Quick demo:**
```bash
python3 scripts/encode_trading_order.py
```

**JSON-driven encoding:**
```bash
python3 scripts/encode_payload.py \
  --schema schema/examples/trading.blink \
  --type Trading:OrderEvent \
  --input schema/examples/order_event.json
```

**Decoding:**
```bash
python3 scripts/decode_payload.py \
  --schema schema/examples/trading.blink \
  --input /path/to/payload.bin
```

**Advanced decoding options:**
```bash
# Decode hex string from stdin
echo "a1b2c3" | python3 scripts/decode_payload.py \
  --schema schema/examples/trading.blink \
  --input - --hex

# Pretty print with custom indentation
python3 scripts/decode_payload.py \
  --schema schema/examples/trading.blink \
  --input /path/to/payload.bin \
  --indent 4 --sort-keys

# Output in Tag or XML format
python3 scripts/decode_payload.py \
  --schema schema/examples/trading.blink \
  --input /path/to/payload.bin \
  --format tag
```

### Native Binary

The `blink.codec.native` module provides the Native Binary format, which uses fixed-width fields with predictable offsets for faster encoding/decoding at the cost of larger message sizes.

**Key features:**
- Fixed-width fields at predictable offsets
- Little-endian byte order
- Relative offsets for variable-sized data
- Optimized for speed over size

**Encoding:**
```python
from blink.codec import native
from blink.runtime.values import Message
from blink.schema.model import QName

message = Message(
    type_name=QName("Trading", "Order"),
    fields={"Symbol": "AAPL", "Price": 150.25, "Quantity": 100}
)
binary_data = native.encode_native(message, registry)
```

**Decoding:**
```python
decoded, offset = native.decode_native(binary_data, registry)
```

**When to use Native vs Compact:**
- **Native**: When encoding/decoding speed is critical and bandwidth is not a constraint
- **Compact**: When message size matters (network transmission, storage)
```

### Tag Format

The `blink.codec.tag` module provides encoding/decoding for the human-readable Tag format.

**Tag format syntax:**
```
@Type|field=value|field=value|[ extension ]
```

**Encoding:**
```python
from blink.codec import tag
from blink.runtime.values import Message
from blink.schema.model import QName

message = Message(
    type_name=QName("Trading", "Order"),
    fields={"Symbol": "AAPL", "Price": 150.25, "Quantity": 100}
)
tag_string = tag.encode_tag(message, registry)
print(tag_string)  # @Trading:Order|Symbol=AAPL|Price=150.25|Quantity=100
```

**Decoding:**
```python
decoded = tag.decode_tag(tag_string, registry)
```

### JSON Mapping

The `blink.codec.jsonfmt` module provides JSON encoding/decoding with Blink-specific features.

**Encoding:**
```python
from blink.codec import jsonfmt
from blink.runtime.values import Message
from blink.schema.model import QName

message = Message(
    type_name=QName("Trading", "Order"),
    fields={"Symbol": "AAPL", "Price": 150.25, "Quantity": 100}
)
json_str = jsonfmt.encode_json(message)
print(json_str)
# {"$type": "Trading:Order", "Symbol": "AAPL", "Price": 150.25, "Quantity": 100}
```

**Decoding:**
```python
decoded = jsonfmt.decode_json(json_str, registry)
```

**Stream decoding:**
```python
messages = jsonfmt.decode_json_stream(json_lines, registry)
```

### XML Mapping

The `blink.codec.xmlfmt` module provides XML encoding/decoding with Blink namespace support.

**Encoding:**
```python
from blink.codec import xmlfmt
from blink.runtime.values import Message
from blink.schema.model import QName

message = Message(
    type_name=QName("Trading", "Order"),
    fields={"Symbol": "AAPL", "Price": 150.25, "Quantity": 100}
)
xml_str = xmlfmt.encode_xml(message, registry)
print(xml_str)
# <ns0:Order xmlns:ns0="Trading"><Symbol>AAPL</Symbol><Price>150.25</Price><Quantity>100</Quantity></ns0:Order>
```

**Decoding:**
```python
decoded = xmlfmt.decode_xml(xml_str, registry)
```

## Dynamic Schema Exchange

The `blink.dynschema.exchange` module provides dynamic schema exchange functionality, allowing runtime schema updates via reserved type IDs (16000-16383).

**Creating a schema exchange registry:**
```python
from blink.dynschema.exchange import create_schema_exchange_registry

registry = create_schema_exchange_registry()
```

**Applying schema updates:**
```python
from blink.dynschema.exchange import decode_stream_with_schema_exchange

# Decode a stream that may contain schema transport messages
messages = decode_stream_with_schema_exchange(buffer, registry)
# Schema transport messages are applied automatically, only application messages are returned
```

**Schema Management CLI:**
```bash
# Validate a schema
python3 scripts/schema_manager.py validate \
  --schema schema/examples/trading.blink

# Export schema to JSON
python3 scripts/schema_manager.py export \
  --schema schema/examples/trading.blink \
  --output schema.json --pretty

# Create a GroupDecl message
python3 scripts/schema_manager.py create-group-decl \
  --ns Test --name MyType --id 100 --hex

# Apply schema transport messages
python3 scripts/schema_manager.py apply \
  --schema schema/examples/trading.blink \
  --input updates.bin
```

## Testing

Run the test suite:
```bash
python3 -m pytest tests -v
```

Run with coverage:
```bash
python3 -m pytest tests --cov=blink --cov-report=term-missing
```

## Development

The project includes a `.devcontainer` configuration for VS Code.

## Status

- ✅ Schema parser/resolver
- ✅ Compact Binary codec
- ✅ Native Binary codec (NEW!)
- ✅ Tag format codec
- ✅ JSON mapping codec
- ✅ XML mapping codec
- ✅ Dynamic schema exchange
- ✅ CLI tooling
- ✅ Property-based tests with Hypothesis
- ✅ 167 tests passing (14 Native Binary tests)
- ✅ 86% test coverage
