import json
from jsonschema import Draft7Validator
from pathlib import Path

SCHEMA_PATH = Path("schemas/question_paper.schema.json")

with open(SCHEMA_PATH) as f:
    _schema = json.load(f)

validator = Draft7Validator(_schema)

def validate_or_raise(payload: dict):
    errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
    if errors:
        msgs = [
            f"{'/'.join(map(str, e.path))}: {e.message}"
            for e in errors
        ]
        raise ValueError("Schema validation failed: " + " | ".join(msgs))