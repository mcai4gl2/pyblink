NEXT ACTION PROMPT: After opening the repo, ask me "Read NEXT_STEP and continue" so I load this file and resume the plan.

# Next Steps for PyBlink (Phase 1 Completion → Phase 2 Kickoff)

This document summarizes outstanding work after comparing `SPEC_ENHANCED.md` with the original Blink specs (`specs/` PDFs). Focus areas combine missing Phase 1 tasks plus Phase 2 deliverables (Tag/JSON codecs, CLI tooling, dynamic schema exchange) that will unblock higher-level integration.

## Schema + Runtime
1. **Schema Transport Messages**: Implement encode/decode helpers for `GroupDecl`, `GroupDef`, `Define`, etc., enabling schema exchange workflows. Requires registry mutation APIs and persistence of schema annotations per spec (Section 9).
2. **Incremental Annotations (Advanced)**: Parser handles them, but resolver must apply schema-level annotations across multiple schema files in the precise order outlined in Appendix A. Add tests covering multi-file merges + clashing annotations.
3. **Static/Optional Groups**: Codec now handles optional static groups via presence bytes; confirm conformance with Blink spec W13 (presence byte only 0x01/0xC0). Add negative tests for invalid presence markers.

## Compact Binary Codec
1. **Dynamic Group Nullability**: Nulls currently piggyback on frame encoding; implement spec-compliant nullable length preamble for dynamic fields and add tests (W14 handling for unknown type IDs).
2. **Extension Blocks**: Extensions now encode as sequences of dynamic groups; ensure we skip unknown type IDs gracefully in permissive mode and expose extension iterators to callers (per Section 5).
3. **Error Classification**: Audit codec errors against spec’s strong/weak error table (Section 5). Annotate `DecodeError` vs `RegistryError` to surface strong errors while allowing weak errors to be logged/skipped.

## Tag / JSON / XML Codecs (Phase 2)
1. **Tag Format**: Implement encoding/decoding with escaping rules described in Section 6. Add property-based tests for multi-line field ordering and reserved characters.
2. **JSON Mapping**: Build JSON codec per Section 7, including numeric thresholds (`|mantissa| < 1e15`), float special tokens (“NaN”, “Inf”), and binary fallback (UTF-8 vs hex array). Reuse `Message` model to avoid duplicating validation logic.
3. **XML Mapping**: Parse/serialize XML documents with Blink namespaces and binary attributes (Section 8). This can layer atop the JSON codec once stable.

## Dynamic Schema Exchange
1. **Transport Flow**: Use the Blink schema (`schema/blink.blink`) to encode/decode schema updates (GroupDecl/GroupDef). Implement registry mutation APIs and ensure they’re thread-safe or documented as single-threaded (per spec).
2. **Decoder Flow**: Extend `decode_message` so frames with reserved type IDs (16000-16383) update the registry before emitting application messages.
3. **Versioning/Constraints**: Enforce spec constraints (e.g., unique type IDs, no inheritance cycles) when applying schema updates. Add tests using sample schema updates derived from official PDFs.

## CLI + Tooling
1. **Decode CLI Enhancements**: `scripts/decode_payload.py` currently dumps JSON but lacks friendly formatting for extensions. Add pretty-print options and ability to decode stdin hex strings.
2. **Schema Management CLI**: Provide a utility that applies schema transport messages (GroupDecl/GroupDef) to on-disk JSON schema snapshots for easier debugging.
3. **Automation**: Add Makefile/Task entries (or devdocker tasks) for running encode/decode demos, schema compilation checks, and full codec test suites.

## Documentation
1. **README Enhancements**: Document new scripts, Blink transport workflow, and instructions for running encode/decode demos with schema exchange messages.
2. **Spec Alignment**: Update `SPEC_ENHANCED.md` with milestone tracking for Tag/JSON/XML codecs, dynamic schema exchange, and CLI coverage. Include explicit acceptance criteria for Phase 2 deliverables.
3. **Examples**: Provide additional sample payloads (e.g., Quote, Trade) to illustrate optional/dynamic fields and extensions.

## Testing / QA
1. **Property Tests**: Use Hypothesis/fuzzing to generate random integer values for VLC encode/decode, sequences, and optional fields, ensuring codec stability across edge cases.
2. **Interop Fixtures**: If available, import Blink reference fixtures (e.g., from official docs) to validate binary compatibility.
3. **Coverage Reporting**: Enable `pytest --cov` (per SPEC) and ensure new codecs/CLIs maintain ≥80% coverage.

## Stretch Goals (Phase 3)
1. **Dynamic Schema Exchange CLI**: Provide a live decoder that applies schema updates on the fly and emits decoded messages, showcasing end-to-end schema evolution.
2. **Native Binary Codec**: Explore optional native format after Compact Binary, Tag, JSON, XML stabilize.
3. **Integration with Agents**: Once stable, expose encode/decode utilities through the repo’s agent tooling (`agents/`) for reuse across other projects.

These steps will complete Phase 1 requirements (full Compact Binary support) and set up Phase 2/3 deliverables (human-readable codecs, schema exchange tooling).***
