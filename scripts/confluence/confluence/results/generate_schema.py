"""."""

from pathlib import Path

from .factory import generate_schema_as_json

if __name__ == "__main__":
    path = Path("src/ska_ser_skallop/confluence/schemas/results-schema.json")
    name = "https://gitlab.com/ska-telescope/ska-ser-skallop/results-schema.json"
    generate_schema_as_json(path, name)
