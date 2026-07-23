# Benchmark Task RW3 - pydantic

**Repo:** pydantic/pydantic (pure-Python package under `pydantic/`)

## Issue #12424: Fields with `exclude_if` should not be required in serialization JSON schema

### Description (verbatim, trimmed)

I've been happily using the new `exclude_if` feature, but it's not quite behaving as expected.

Expectation: the JSON schema in serialization mode marks fields with `exclude_if` as optional. The JSON schema accurately describes the structure of the serialization output.

Reality: such fields are marked as required, even though they may be absent in the actual output.

For example, consider this model:

```python
class MyModel(pydantic.BaseModel):
    field: Annotated[str, pydantic.Field(exclude_if=lambda x: x == "null")]
```

Its input and output JSON schema are as follows, with the `field` marked as `required`:

```json5
{"properties": {"field": {"title": "Field", "type": "string"}},
 "required": ["field"],  // <--
 "title": "MyModel",
 "type": "object"}
```

However, dumping values like `MyModel(field="null")` would result in an empty dict `{}` which
violates the promised schema. Given the model, I'd have expected the `field` to be required in
validation mode, but optional in serialization mode.

### Minimal repro

```python
from typing import Annotated
import pydantic

class MyModel(pydantic.BaseModel):
    field: Annotated[str, pydantic.Field(exclude_if=lambda x: x == "null")]

# Serialization-mode schema currently (wrongly) lists `field` as required:
print(MyModel.model_json_schema(mode="serialization"))
# -> {..., 'required': ['field'], ...}   # BUG: should be absent from `required`

# But the output can be empty:
print(MyModel(field="null").model_dump())   # -> {}
```

Expected: in `mode="serialization"`, a field with `exclude_if` set must NOT appear in the
schema's `required` list (it can be absent from the serialized output). Validation-mode schema
is unchanged. This must also respect the `json_schema_serialization_defaults_required` config
flag and continue to work for plain `exclude=True`, defaults, and typed-dict fields.

## Rules

- Fix the bug in the library source (the pure-Python `pydantic/` package). Do NOT modify test files.
- Hidden maintainer-written tests for this exact bug will grade you.
- The virtualenv at `.venv` is ready (`.venv/Scripts/python`).
- Wall-clock time counts. Hard cap 10 minutes.

Run the existing suite with the venv's pytest, e.g.:
`.venv/Scripts/python -m pytest tests/test_json_schema.py -q`
