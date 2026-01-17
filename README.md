# PyBlink

PyBlink is a Blink protocol playground housed inside `py-learn/projects/pyblink`. The current focus is building a schema parser/resolver, Compact Binary codec, and tooling that slots into the repo’s devcontainer workflow.

## Compiling Schemas

Blink schemas (`.blink` files) can be parsed and resolved in a single call via `blink.schema.compile_schema` or by building a `TypeRegistry` directly. A sample trading schema lives under `schema/examples/trading.blink`.

Example usage:

```bash
docker exec -u vscode -w /workspaces/py-learn <container-id> python3 - <<'PY'
from blink.schema import compile_schema_file
from blink.runtime.registry import TypeRegistry

schema = compile_schema_file("projects/pyblink/schema/examples/trading.blink")
registry = TypeRegistry.from_schema(schema)

order = registry.get_group_by_name("Trading:Order")
print("Order fields:", [field.name for field in order.fields])
PY
```

You can also skip the intermediate `Schema` object:

```python
registry = TypeRegistry.from_schema_file("projects/pyblink/schema/examples/trading.blink")
```

These helpers power upcoming codec work (e.g., Compact Binary framing) and keep schema loading consistent across tests and tooling.
## Compact Binary Demo

`blink.codec.compact` supports schema-aware `encode_message`/`decode_message`. Two helpers are available:

1. Quick demo that builds a sample payload in code:
   ```bash
   docker exec -u vscode -w /workspaces/py-learn <container-id> python3 projects/pyblink/scripts/encode_trading_order.py
   ```
   This prints a hex-encoded `OrderEvent` built from in-memory data.

2. JSON-driven CLI that accepts arbitrary payloads:
   ```bash
   docker exec -u vscode -w /workspaces/py-learn <container-id> python3 \
     projects/pyblink/scripts/encode_payload.py \
     --schema projects/pyblink/schema/examples/trading.blink \
     --type Trading:OrderEvent \
     --input projects/pyblink/schema/examples/order_event.json
   ```

   The CLI loads the schema, reads the JSON payload (which can include dynamic groups via `$type` and decimals via `{ "exponent": ..., "mantissa": ... }`), and prints the Compact Binary bytes. Use it as a starting point for integrating codec support into future tools.

To decode Compact Binary back into JSON, use `scripts/decode_payload.py`:

```bash
docker exec -u vscode -w /workspaces/py-learn <container-id> python3 \
  projects/pyblink/scripts/decode_payload.py \
  --schema projects/pyblink/schema/examples/trading.blink \
  --input /path/to/payload.bin
```

Add `--hex` if the input file contains a hex string instead of raw bytes.*** End Patch
