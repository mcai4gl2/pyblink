# Blink Protocol (beta4) – Python Implementation Specification (Enhanced)

**Status**: In progress – Phase 1 schema parser/resolver + runtime foundation completed through 2026‑01‑17
**Audience**: Engineers building/maintaining Blink in Python within `py-learn`
**Scope**: Schema parsing/resolution, Compact Binary codec, Tag + JSON + XML formats, Dynamic Schema Exchange, optional Native codec, repo-compliant workflows

This version augments `SPEC.md` with concrete workflow gating from `.clinerules`, explicit deliverables, and QA expectations. Treat it as the single source of truth when planning work or reviews.

---

## 0. Repository & Workflow Requirements

`projects/pyblink` inherits all py-learn governance. The most relevant items are expanded here so you never need to leave container context or fight CI.

1. **Dev Container or approved automation only.** Every command that mutates files must run through the dev container as user `vscode`:
   ```bash
   docker exec -u vscode -w /workspaces/py-learn <container-id> <command>
   ```
   Failing to do so produces root-owned files that break VS Code sync; fix by `chown -R vscode:vscode /workspaces/py-learn/projects/pyblink` if necessary.

2. **Per-project virtual environment lives inside the container.**
   ```bash
   docker exec -u vscode -w /workspaces/py-learn/projects/pyblink <cid> python3 -m venv .venv
   docker exec -u vscode -w /workspaces/py-learn/projects/pyblink <cid> .venv/bin/pip install -r requirements.txt
   ```
   Never reuse host venv paths; container Python and host Python differ.

3. **Tooling + linting reuse repo defaults.** Black, Ruff, mypy, pytest, ipython, etc. are already in the dev-container image via `tools/requirements.txt`. Do not pin alternate versions locally; if updates are required, change the shared requirements and regenerate the container.

4. **Testing is mandatory and centralized.**
   - Place unit tests in `projects/pyblink/tests/` with pytest discovery.
   - Achieve ≥80% line coverage and 100% on codec critical paths (VLC, framing, schema resolution). Use `pytest --cov=projects/pyblink --cov-report=term-missing` inside the container.
   - Any helper living under `tools/` requires tests under `tools/tests/` per `.clinerules`.

5. **VS Code tasks/launch configs are generated artifacts.** Add/edit per-project Docker tasks via `devdocker.json` or `tools/config.json`, then run:
   ```bash
   docker exec -u vscode -w /workspaces/py-learn <cid> python3 tools/update_vscode_configs.py
   ```
   Never hand-edit `.vscode/*.json`.

6. **Relative paths only in configs.** Avoid `${workspaceFolder}` or host paths; container + host share `py-learn` root intentionally.

7. **CI surfaces repo-wide style + safety checks.** Before opening a PR:
   ```bash
   docker exec -u vscode -w /workspaces/py-learn <cid> python3 -m pytest projects/pyblink/tests -v
   docker exec -u vscode -w /workspaces/py-learn <cid> ruff check projects/pyblink
   docker exec -u vscode -w /workspaces/py-learn <cid> black --check projects/pyblink
   docker exec -u vscode -w /workspaces/py-learn <cid> mypy projects/pyblink
   ```

---

## 1. Goals, Non-Goals, and Deliverables

### Goals
- Parse Blink schema text (beta4) into a fully resolved in-memory schema (namespaces, inheritance, annotations).
- Encode/decode Blink Compact Binary with strict + permissive error handling.
- Provide Tag, JSON, XML human-readable representations.
- Support schema-driven runtime model (static groups, dynamic groups, nullable fields, sequences, message extensions, enums, decimals, time types).
- Offer optional Dynamic Schema Exchange + Native codec when capacity allows.

### Non-Goals
- Transport framing (network sockets, disk persistence) beyond codec outputs.
- Schema authoring UI/DSL validation beyond spec compliance.
- Application routing, state machines, or persistence layers.

### Deliverables
1. **Python package `projects/pyblink/blink/`** following the layout below.
2. **Test suite** under `projects/pyblink/tests` covering positive, negative, and fuzz-ish cases for codecs.
3. **Developer docs** (README updates, this spec) describing commands for schema compilation/testing.
4. **Optional CLI scripts** under `projects/pyblink/scripts/` that exercise codecs; if added, ensure they are wired through repo tooling.

---

## 2. Repository Layout (Recommended)

```
projects/pyblink/blink/
├── schema/
│   ├── lexer.py
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

- Add `__init__.py` files to expose top-level APIs (`blink.schema`, `blink.codec.compact`, etc.).
- Keep generated artifacts (e.g., schema fixtures) under `projects/pyblink/tests/fixtures`.

---

## 3. Schema Model (Authoritative)

### 3.1 Qualified Names
- Accept `name` or `namespace:name`.
- Resolve with precedence: explicit namespace → current schema namespace → null namespace.
- Internal type:
  ```python
  @dataclass
  class QName:
      namespace: str | None
      name: str
  ```

### 3.2 Types
- **Primitives:** `u8/u16/u32/u64`, `i8/i16/i32/i64`, `bool`, `f64`, `decimal`, `millitime`, `nanotime`, `date`, `timeOfDayMilli`, `timeOfDayNano`. Represent as Python ints/floats with decimal stored as `(exponent, mantissa)` tuple or dedicated `DecimalValue` dataclass.
- **Byte-ish:** `string` → UTF-8 `str`; `binary` → `bytes`; `fixed(N)` → `bytes` exactly N bytes.
- **Composites:**
  - `sequence<T>` → `list[T]` (no nested sequences allowed).
  - `static group` → dataclass/dict capturing resolved fields.
  - `dynamic group` / `object` → runtime `Message` referencing group types.
- Validate type references at resolution time; raise schema errors (strong) for missing definitions.

### 3.3 Enums
- Map symbol → `int32`.
- Provide helper to convert between symbol/number and fail fast on duplicates.

### 3.4 Group + Field Definitions
- `GroupDef` contains `qname`, optional numeric `type_id`, optional `super`, field list, annotations.
- Field linearization = `super.fields + local.fields`.
- `FieldDef` stores `name`, `Type`, `optional: bool`, annotation dict.

### 3.5 Annotations
- Inline annotations apply immediately; incremental annotations override/extend.
- Preserve as opaque `Dict[QName, str]` for codecs/metadata consumers.

---

## 4. Runtime Message Model

- `Message(type: QName, fields: Dict[str, Value], extension: list[Message])`.
- Values: primitives, bytes, strings, lists, `Message`, `StaticGroupValue`, `DecimalValue`.
- Optional fields omitted entirely; treat `None` as invalid at runtime.
- Provide helper constructors for schema-driven validation (throw `DecodeError` for missing required fields).

---

## 5. Compact Binary Encoding

### 5.1 Framing
```
message :=
  length(u32 VLC)
  typeId(u64 VLC)
  fields...
  extension?
```
- `length` is byte count of the remainder. Validate actual bytes consumed.

### 5.2 VLC
- Variable-length coding for signed/unsigned ints.
- `NULL` encoded as byte `0xC0`.
- API surface:
  ```python
  encode_vlc(value: int | None) -> bytes
  decode_vlc(buffer: memoryview, offset: int) -> tuple[int | None, int]
  ```
- Provide fuzz/round-trip tests hitting boundary values (`0`, `-1`, `2**63-1`).

### 5.3 Field Rules
- Integers/bools/enums/time = VLC integer (signed via two’s complement where applicable).
- String/Binary = `length(u32 VLC)` + payload bytes. Nullable → `length == NULL`.
- Fixed = raw bytes (non-nullable) or `presence byte (0x01|0xC0)` + bytes.
- Decimal = exponent VLC + mantissa VLC (nullable exponent → missing value).
- Static group = inline encoding of resolved fields, optional presence byte for nullable.
- Dynamic group = `length + typeId + fields + extension`, nullable via nullable length.
- Sequence = `count(u32 VLC)` + item encodings, nullable via nullable count.

### 5.4 Extensions
```
extension :=
  count(u32 VLC)
  dynamic_group[count]
```
- Codec must skip unknown type IDs gracefully while leaving buffer at extension boundary.

### 5.5 Errors
- **Strong**: truncated frame, missing required field, invalid frame length.
- **Weak**: unknown type id, invalid UTF-8, out-of-range ints.
- Decoder exposes `strict` (raise on weak errors) vs `permissive` (skip/log) modes.

---

## 6. Tag Format
- Syntax: `@Type|field=value|field=value|[ extension ]` (one per line, order irrelevant).
- Escape reserved chars `|[]{};#\` using `\n`, `\xNN`, `\uXXXX`, `\UXXXXXXXX`.
- Binary/fixed values expressed as `[3e 6d 4a]`; fixed lengths validated strictly.

---

## 7. JSON Mapping
- Message object requires `$type` and optional `$extension` array.
- Integers with `|mantissa| < 1e15` remain numeric; others serialized as decimal strings.
- `NaN`/`Inf`/`-Inf` use quoted tokens.
- Binary values encode as UTF-8 strings when valid, or list of hex strings otherwise.

---

## 8. XML Mapping
- Base element `<ns:Type>` with child elements per field.
- Extensions live under `<blink:extension>` containing nested message elements.
- Binary fields default to text for UTF-8, otherwise `<field binary="yes">deadbeef</field>`.
- Namespace URI equals Blink namespace literal.

---

## 9. Dynamic Schema Exchange
- Reserved type-id range `16000–16383` for schema transport messages (`GroupDecl`, `GroupDef`, `TypeDef`, `SchemaAnnotation`).
- Decoder flow: decode frame → apply schema updates if message falls in reserved range → retry decode with updated registry.
- Registry must be thread-safe if used concurrently; otherwise document single-thread assumption.

---

## 10. Native Binary Format (Optional)
```
u32 size
u64 typeId
u32 extensionOffset
fixed-width fields
variable data area
```
- Variable fields referenced via relative offsets; optional fields have presence byte near fixed block.
- Only pursue after Compact Binary + human formats stabilize.

---

## 11. Public API Contract

### Schema
```
Schema.parse(text: str) -> Schema
Schema.merge(other: Schema) -> Schema
Schema.resolve() -> ResolvedSchema
```

### Registry
```
Registry(schema: ResolvedSchema)
Registry.get_group_by_id(type_id: int) -> GroupDef
Registry.get_group_by_name(qname: QName) -> GroupDef
```

### Compact Codec
```
encode(message: Message, registry: Registry) -> bytes
decode_one(buffer: bytes | memoryview, offset: int = 0, *, strict: bool = True) -> tuple[Message, int]
decode_stream(buffer: bytes | BinaryIO, *, strict: bool = True) -> Iterator[Message]
```

Expose Tag/JSON/XML helpers with symmetrical encode/decode functions.

---

## 12. Testing & QA Expectations
1. Primitive encode/decode round-trips (per type, signed/unsigned boundaries).
2. Optional field omission vs explicit values.
3. Inheritance linearization + overrides.
4. Static group nesting depth tests.
5. Dynamic group sequence encoding/decoding.
6. Extension skipping, unknown type IDs, strict/permissive toggles.
7. Tag escaping coverage (reserved chars, unicode).
8. JSON numeric thresholds + special float tokens.
9. XML binary mode switching.
10. Dynamic schema exchange applying incremental updates.
11. Negative-path tests (truncated buffers, invalid VLC, invalid UTF-8) raising `DecodeError`.
12. Integration tests comparing reference fixtures (if available) to ensure compatibility with Blink beta4 examples.

Surface coverage metrics in CI; fail build if thresholds drop.

---

## 13. Recommended Milestones
- **Phase 1**: schema parser/resolver, runtime model, Compact Binary encode/decode, registry tests.
- **Phase 2**: Tag + JSON codecs, CLI tooling, golden tests.
- **Phase 3**: Dynamic schema exchange, XML mapping, Native codec.

Each phase should land as incremental PRs respecting container + testing workflow above.

---

## 14. Licensing

Specification derives from Blink beta4 public docs. Confirm downstream licensing compatibility before distributing compiled schemas or binaries; document any third-party assets introduced (schemas, fixtures) in `LICENSE-THIRD-PARTY` if required.

---

## 15. Current Status (2026-01-17)

- **Runtime foundation ready**: Added `blink.runtime` with error types, registry, and value containers (`DecimalValue`, `StaticGroupValue`, `Message`) to support schema-driven encoding/decoding.
- **Schema parser + resolver landed**: Built a tokenizer/parser covering enums, type defs, sequences, annotations (inline + incremental), and object/dynamic references, then fed it into a resolver that merges incremental annotations, lazy-loads enums/types, and enforces Blink constraints.
- **Schema helpers + samples**: Introduced `compile_schema(_file)` + `TypeRegistry.from_schema_*`, a documented trading schema example, and README guidance for quickly compiling `.blink` files in the devcontainer.
- **Compact Binary framing**: Finished stop-bit VLC helpers plus schema-aware `encode_message`/`decode_message` capable of handling ints, decimals, enums, strings, static groups (with presence bytes), dynamic/object groups (nullable length), sequences of those types, and extension blocks; trading-schema round trips (OrderEvent, BulkOrder) and extensions are covered by pytest.
- **CLI tooling**: Added JSON-driven encoding/decoding scripts (`scripts/encode_payload.py`, `scripts/decode_payload.py`) and sample payloads so devs can convert between dicts and Compact Binary directly inside the devcontainer.
- **Testing wired**: Devcontainer pytest invocation (`python3 -m pytest projects/pyblink/tests -q`) now exercises VLC, parser/resolver, compile helpers, Compact Binary framing, and CLI-backed fixtures.
