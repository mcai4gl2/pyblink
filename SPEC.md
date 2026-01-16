# Blink Protocol (beta4) – Python Implementation Specification

**Status**: Draft (implementation-oriented)  
**Audience**: Engineers implementing Blink in Python  
**Scope**: Schema parsing, Compact Binary codec, Tag/JSON/XML formats, Dynamic Schema Exchange, optional Native codec

---

## 0. py-learn Repository Integration

This spec lives inside the `py-learn` monorepo and inherits the global development rules described in `.clinerules`. The highlights relevant to `projects/pyblink`:

- **Always work inside the Dev Container**. Run commands via `docker exec -u vscode -w /workspaces/py-learn <container> <command>` so generated files stay owned by the `vscode` user and remain editable on the host.
- **Virtual environments are container-native**. Create and activate venvs from inside the container (e.g., `python3 -m venv projects/pyblink/.venv && projects/pyblink/.venv/bin/pip install -r requirements.txt`).
- **Testing is mandatory**. Every new tool/utility under `tools/` or project-specific helper must have pytest coverage (target ≥80%). Place `pyblink` tests under `projects/pyblink/tests/` and wire them into the root `pytest` invocation.
- **VS Code configs are auto-generated**. When `pyblink` needs new tasks or launchers, update `tools/config.json` or per-project `devdocker.json` and run `python tools/update_vscode_configs.py` inside the container rather than editing `.vscode/*.json` directly.
- **Docker assets follow repo conventions**. Additional development containers or tasks for `pyblink` should reuse the shared images defined under `.devcontainer/` and `tools/config.json`, using relative paths (avoid `${workspaceFolder}` in configs).
- **Follow repo-wide linting/tooling**. Formatting, linting, and type checking rely on the shared toolchain baked into the container image (`tools/requirements.txt`). New scripts should integrate with this toolchain instead of vendoring alternatives.

This document consolidates the Blink beta4 specifications into a single, actionable implementation spec suitable for bootstrapping a Python library.

---

## 1. Goals and Non-Goals

### 1.1 Goals
- Parse Blink schema definitions into a resolved in-memory schema.
- Encode and decode Blink **Compact Binary** messages.
- Support:
  - nullable fields
  - inheritance
  - static groups, dynamic groups
  - sequences
  - message extensions
- Provide human-readable interchange formats:
  - Tag format
  - JSON mapping
  - XML mapping
- Optionally support:
  - Dynamic Schema Exchange
  - Native binary format

### 1.2 Non-Goals
- Transport/session framing (TCP/UDP/WebSocket/etc.).
- Application-level routing or persistence.
- Schema authoring tools or IDE integrations.

---

## 2. Repository Layout

Recommended structure:

```
blink/
├── schema/
│   ├── parser.py
│   ├── ast.py
│   ├── model.py
│   ├── resolve.py
│   └── annotations.py
├── codec/
│   ├── compact.py
│   ├── vlc.py
│   ├── tag.py
│   ├── jsonfmt.py
│   ├── xmlfmt.py
│   └── native.py        # optional
├── dynschema/
│   └── exchange.py
├── runtime/
│   ├── values.py
│   ├── registry.py
│   ├── io.py
│   └── errors.py
└── tests/
```

---

## 3. Schema Model

### 3.1 Names

A name is:
- `name`
- or `namespace:name`

Internal representation:

```
QName:
  namespace: Optional[str]
  name: str
```

Resolution order:
1. Explicit namespace
2. Current schema namespace
3. Null namespace

---

### 3.2 Types

#### 3.2.1 Primitive Types

| Type | Python representation |
|----|----|
| u8, u16, u32, u64 | int |
| i8, i16, i32, i64 | int |
| bool | bool |
| f64 | float |
| decimal | (exponent:int, mantissa:int) |
| millitime | int |
| nanotime | int |
| date | int |
| timeOfDayMilli | int |
| timeOfDayNano | int |

---

#### 3.2.2 Byte Types

| Type | Python |
|----|----|
| string | str (UTF-8) |
| binary | bytes |
| fixed(N) | bytes (exact length) |

---

#### 3.2.3 Composite Types

- `sequence<T>` → `list[T]`
- `static group` → dict or StaticGroupValue
- `dynamic group` → Message
- `object` → any dynamic group

Constraints:
- No sequence of sequence.
- Dynamic group must reference a group type.
- Static group must not be dynamic.

---

### 3.3 Enum Types

Enum symbols map to explicit `int32` values.

```
EnumType:
  symbols: Dict[str, int]
```

---

### 3.4 Group Definition

```
GroupDef:
  qname: QName
  type_id: Optional[int]
  super: Optional[GroupRef]
  fields: List[FieldDef]
  annotations: Dict[QName, str]
```

Inheritance:
- Fields are linearized as:
  ```
  super.fields + local.fields
  ```

---

### 3.5 Field Definition

```
FieldDef:
  name: str
  type: Type
  optional: bool
  annotations: Dict[QName, str]
```

---

### 3.6 Annotations

- Inline annotations apply immediately.
- Incremental annotations override inline.
- Stored as opaque key/value pairs.

---

## 4. Runtime Message Model

### 4.1 Message

```
Message:
  type: QName
  fields: Dict[str, Value]
  extension: List[Message]
```

### 4.2 Values

```
Value :=
  int | float | bool | str | bytes |
  List[Value] |
  Message |
  StaticGroupValue |
  DecimalValue
```

Optional fields are **absent**, not set to None.

---

## 5. Compact Binary Encoding

### 5.1 Message Frame

```
message :=
  length(u32 VLC)
  typeId(u64 VLC)
  fields...
  extension?
```

- `length` = number of bytes following it.

---

### 5.2 VLC Encoding

- Variable Length Coding for integers.
- NULL encoded as single byte `0xC0`.

API:

```
encode_vlc(value: int | NULL) -> bytes
decode_vlc(buffer, offset) -> (value | NULL, new_offset)
```

---

### 5.3 Field Encoding Rules

#### Integer / Bool / Enum / Time
- Encoded as VLC integer.
- Signed values encoded as two’s complement.

#### String / Binary
```
length(u32 VLC) + data
```
Nullable:
- length = NULL → field absent

#### Fixed
- Non-nullable: raw bytes
- Nullable: presence byte (0x01 or 0xC0) then bytes

#### Decimal
```
exponent(i8 VLC)
mantissa(i64 VLC)
```
Nullable: exponent NULL → no mantissa

#### Static Group
- Inline encode fields
- Nullable: presence byte

#### Dynamic Group
```
length + typeId + fields + extension
```
Nullable: nullable length

#### Sequence
```
count(u32 VLC) + items...
```
Nullable: nullable count

---

### 5.4 Extensions

If message body has remaining bytes:
```
extension :=
  count(u32 VLC)
  dynamic_group[count]
```

Unknown extension types must be skipped safely.

---

### 5.5 Error Handling

**Strong Errors**
- Truncated message
- Missing required fields
- Invalid framing

**Weak Errors**
- Unknown type id
- Invalid UTF-8
- Out-of-range values

Decoder must support strict / permissive modes.

---

## 6. Tag Format

### 6.1 Syntax

```
@Type|field=value|field=value|[ extension ]
```

- One message per line.
- Field order irrelevant.
- Optional fields omitted.

---

### 6.2 Escaping

Reserved chars: `|[]{};#\`

Escapes:
- `\n`
- `\xNN`
- `\uXXXX`
- `\UXXXXXXXX`

---

### 6.3 Binary / Fixed

- Hex list: `[3e 6d 4a]`
- Fixed must match exact size.

---

## 7. JSON Mapping

### 7.1 Message Object

```
{
  "$type": "Ns:Name",
  "field": value,
  "$extension": [ ... ]
}
```

- Optional fields omitted.

---

### 7.2 Numeric Rules

- Integers |mantissa| < 1e15 → JSON number
- Otherwise → string
- NaN / Inf → `"NaN"`, `"Inf"`, `"-Inf"`

---

### 7.3 Binary

- UTF-8 valid → string
- Otherwise → array of hex strings

---

## 8. XML Mapping

### 8.1 Message Element

```
<ns:Type>
  <field>value</field>
  <blink:extension>...</blink:extension>
</ns:Type>
```

Namespaces:
- Blink namespace URI = namespace name string

---

### 8.2 Binary

- UTF-8 → text
- Otherwise:
```
<field binary="yes">3e6d4a</field>
```

---

## 9. Dynamic Schema Exchange

### 9.1 Reserved Type IDs

```
16000 – 16383
```

Includes:
- GroupDecl
- GroupDef
- TypeDef
- SchemaAnnotation

---

### 9.2 Decoder Flow

1. Decode message
2. If schema message → apply to registry
3. Else → decode using current schema

Schema registry must be mutable.

---

## 10. Native Binary Format (Optional)

### 10.1 Layout

```
u32 size
u64 typeId
u32 extensionOffset
fixed-width fields
data area
```

- Variable fields use relative offsets.
- Optional fields have presence byte.

---

## 11. Public API

### 11.1 Schema

```
Schema.parse(text) -> Schema
Schema.merge(other)
Schema.resolve() -> ResolvedSchema
```

### 11.2 Registry

```
Registry(schema)
get_group_by_id(type_id)
get_group_by_name(qname)
```

### 11.3 Compact Codec

```
encode(message) -> bytes
decode_one(buffer, offset) -> (message, new_offset)
decode_stream(bytes) -> Iterator[Message]
```

---

## 12. Conformance Tests

Required test coverage:
1. Primitive encode/decode
2. Optional fields
3. Inheritance
4. Static group nesting
5. Dynamic group sequences
6. Extensions
7. Tag escaping
8. JSON numeric edge cases
9. XML binary handling
10. Dynamic schema exchange

---

## 13. Recommended Implementation Order

**Phase 1**
- Schema parser
- Compact binary codec
- Registry

**Phase 2**
- Tag format
- JSON mapping

**Phase 3**
- Dynamic schema exchange
- XML mapping
- Native codec

---

## 14. License and Compatibility

This specification is derived from Blink beta4 public specifications.
Ensure license compatibility if distributing binaries or schema definitions.
