# PyBlink Specification Review

## Status Update (2026-01-20)

**Test Results:** ✅ 167 tests passing (was 139 passed, 14 failed initially)

**High-Severity Issues Fixed:**
- ✅ f64 encoding/decoding - IEEE 754 conversion implemented
- ✅ Nullable fixed fields - Presence byte handling added
- ✅ Tag format syntax - Corrected to spec (Y/N booleans, [...] sequences, semicolons)
- ✅ Tag format value rules - Boolean tokens and formatting fixed
- ✅ JSON mapping - Stream arrays, decimal numbers, time/date strings implemented
- ✅ XML structure and namespace - Corrected namespace, root wrapper, binary handling

**Medium-Severity Issues Fixed:**
- ✅ JSON hex list decoding - Now accepts whitespace groups
- ✅ XML binary handling - Fixed UTF-8 text encoding and binary attribute logic

**New Features Implemented:**
- ✅ **Native Binary format** - **COMPLETE** with all 15 tests passing
  - Fixed-width fields with predictable offsets
  - Little-endian byte order, relative offsets for variable data
  - All primitive types, sequences, static/dynamic groups, extensions
  - **Inline strings (max-size 1-255)** - Now fully supported with schema annotations
  - **String/binary max-size annotations** - Schema model updated to accept `string(N)` and `binary(N)`

**Issues Not Yet Addressed:**
- Schema exchange (partial implementation, no failing tests)
- Extensions skipping unknown types
- Dynamic group compatibility checks
- UTF-8 decoding weak error handling
- Optional fields presence semantics
- Strict/permissive propagation

See `devlogs/2026-01-20.md` for technical implementation details.

---

## Status Update (2026-01-22)

**Playground Enhancement:**
- ✅ Updated default example to demonstrate nested classes and subclasses
- ✅ Replaced simple Person schema with Company/Employee/Manager hierarchy
- ✅ All format conversions tested and validated

See `devlogs/2026-01-22.md` for details on the example update.

---

## Scope and sources checked
- `projects/pyblink/SPEC.md`
- `projects/pyblink/specs/BlinkSpec-beta4.txt`
- `projects/pyblink/specs/*.pdf` (text extracted via `pypdf` in the devcontainer)
- `projects/pyblink/schema/blink.blink`
- Code under `projects/pyblink/blink/`

## Findings

### High severity
- **f64 encoding/decoding is missing and incompatible with the spec.** The compact codec treats all primitives (except bool/decimal) as VLC integers and rejects non-int values; it never converts floating point values to IEEE 754 bit patterns as required by Blink beta4 (f64 is encoded as a u64 bit pattern via VLC). This means encoding floats will fail and decoding yields integers instead of floats. Files: `projects/pyblink/blink/codec/compact.py:186-208`, `projects/pyblink/blink/codec/compact.py:411-422`.
- **Nullable fixed fields are encoded/decoded incorrectly.** The spec requires a presence byte (0x01 or 0xC0) before fixed bytes. The implementation uses a nullable VLC for `None` and omits the presence byte when present, and the decoder always consumes fixed bytes with no presence byte handling. This will misparse all nullable fixed fields. Files: `projects/pyblink/blink/codec/compact.py:211-228`, `projects/pyblink/blink/codec/compact.py:425-441`.
- **Schema exchange only partially implemented (GroupDecl/GroupDef) and does not update group fields.** `apply_schema_update` only supports GroupDecl and GroupDef; FieldDef/Define/TypeDef/Annotation messages are rejected, and GroupDef handling only registers IDs, not fields or inheritance. This does not align with the schema exchange spec or the `schema/blink.blink` transport schema. Files: `projects/pyblink/blink/dynschema/exchange.py:92-176`, `projects/pyblink/blink/dynschema/exchange.py:179-238`, `projects/pyblink/schema/blink.blink:1-49`.
- **Schema exchange type IDs in `schema/blink.blink` do not match the PDF Schema Exchange spec.** The PDF spec assigns different IDs for Define/Ref/DynRef/etc. than the repo’s transport schema, so a stream built per the PDF will not decode with the current registry or exchange implementation. Files: `projects/pyblink/schema/blink.blink:5-65`, `projects/pyblink/blink/dynschema/exchange.py:32-86`.
- **Extensions cannot safely skip unknown types.** The spec allows ignoring or selectively decoding extension groups. The implementation always decodes extensions using the registry and fails on unknown type IDs; the `strict` flag on `decode_message` does not apply to extensions. This violates the extension handling requirements and makes streams with new extension types fail. Files: `projects/pyblink/blink/codec/compact.py:135-141`, `projects/pyblink/blink/codec/compact.py:476-482`.
- **Tag format syntax differs from the Tag spec.** Sequences must use `[...]` with semicolon separators, and group field separators are `|`; extensions use `|[...]` with semicolons. The implementation uses `{...}` and commas for sequences and static groups, and commas for extensions, so round-trip Tag compliance is broken. Files: `projects/pyblink/blink/codec/tag.py:157-213`, `projects/pyblink/blink/codec/tag.py:250-340`.
- **Tag format value rules are mismatched.** The spec encodes booleans as `Y`/`N`, supports f64 `Inf/-Inf/NaN`, and formats time/date/timeOfDay as ISO strings. The implementation uses `true/false`, treats f64/time/date as integers, and does not parse the Tag time/date formats. Files: `projects/pyblink/blink/codec/tag.py:136-239`.
- **JSON mapping diverges from the JSON spec.** Streams should be wrapped in a JSON array (not one-object-per-line), time/date types should be strings in Tag format, and decimals should be numbers when |mantissa| < 1e15. The implementation emits newline-delimited objects, encodes decimals only as mantissa/exponent strings, and treats time/date types as integers. Files: `projects/pyblink/blink/codec/jsonfmt.py:47-72`, `projects/pyblink/blink/codec/jsonfmt.py:147-188`, `projects/pyblink/blink/codec/jsonfmt.py:261-273`.

### Medium severity
- **String/binary max-size annotations from the spec are not supported.** Blink allows `string(n)` and `binary(n)` max sizes. The parser accepts sizes, but the model rejects `size` for non-fixed types, so schemas using max sizes will fail to resolve. No validation exists for max-size overflow (weak errors W7/W8). Files: `projects/pyblink/blink/schema/parser.py:333-365`, `projects/pyblink/blink/schema/model.py:67-78`.
- **Dynamic group compatibility checks are missing.** The spec says a dynamic group’s actual type must be compatible with the declared base type (same or derived), otherwise a weak error (W15). The codec never checks that a dynamic group instance conforms to the declared base type during encode or decode. Files: `projects/pyblink/blink/codec/compact.py:284-316`, `projects/pyblink/blink/codec/compact.py:444-455`.
- **JSON hex list decoding is too restrictive.** The JSON spec allows each hex list entry to contain multiple hex pairs with spaces; the decoder only accepts per-byte strings, so valid JSON hex lists will fail to parse. Files: `projects/pyblink/blink/codec/jsonfmt.py:190-201`.
- **XML binary handling is more restrictive than the spec and can mis-decode.** Encoding only emits text for ASCII-safe UTF-8, not all valid UTF-8; valid UTF-8 containing non-ASCII characters is hex-encoded instead of text. Decoding treats any hex-looking string as hex even when `binary="yes"` is absent, which conflicts with the spec’s binary attribute signal. Files: `projects/pyblink/blink/codec/xmlfmt.py:52-66`, `projects/pyblink/blink/codec/xmlfmt.py:206-224`.
- **XML structure and namespace mismatches.** Streams should be wrapped in a single root element; extension elements must use `http://blinkprotocol.org/ns/blink` for the `blink:extension` namespace, but the implementation uses `http://blinkprotocol.org/beta4`. Sequence items for static groups should be field elements under an item element, but the encoder builds nested message elements instead. Files: `projects/pyblink/blink/codec/xmlfmt.py:31-179`.
- **UTF-8 decoding errors are treated as hard failures, not weak errors.** The spec classifies invalid UTF-8 as a weak error, but the compact decoder raises exceptions immediately and does not offer a permissive mode for strings. Files: `projects/pyblink/blink/codec/compact.py:439-441`.

### Low severity
- **Optional fields are present with `None` rather than omitted.** `SPEC.md` says optional fields should be absent in the runtime model, but the decoder populates every field with `None` when null. This is a semantic mismatch with the project spec (not necessarily with Blink itself). Files: `projects/pyblink/blink/codec/compact.py:347-360`, `projects/pyblink/blink/runtime/values.py:41-75`.
- **Strict/permissive handling is only applied to top-level frames.** The `strict` parameter does not propagate to nested dynamic groups or extensions, so permissive decoding is incomplete. Files: `projects/pyblink/blink/codec/compact.py:122-142`, `projects/pyblink/blink/codec/compact.py:444-482`.
- **Native binary format is not implemented.** This is optional per `SPEC.md`, but the Native spec PDF describes a full format not present in the codebase. Files: `projects/pyblink/SPEC.md:39`.

## Suggested focus areas for remediation
- Implement IEEE-754 f64 conversion (pack/unpack to u64 bits via VLC) to align with BlinkSpec beta4.
- Add proper nullable fixed handling (presence byte) and update `_decode_binary` to respect it.
- Expand schema exchange to support FieldDef/Define/TypeDef and construct full GroupDef field sets, including inheritance.
- Reconcile schema exchange type IDs with the Schema Exchange PDF or document the intentional divergence.
- Bring Tag/JSON/XML codecs into alignment with their respective specs (sequence delimiters, boolean tokens, time/date formatting, stream wrappers, extension namespaces).
- Allow `string(n)` and `binary(n)` max-size in the model and enforce weak-error checks.
- Apply strict/permissive handling consistently to dynamic groups and extensions, and allow skipping unknown extension types.
- Align XML binary encoding/decoding with the spec’s `binary="yes"` attribute rules and UTF-8 handling.
