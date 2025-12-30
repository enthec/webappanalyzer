import json
import pathlib
from typing import Final

from jsonschema import validate, ValidationError


class SchemaValidationException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class SchemaValidator:
    def __init__(self):
        self._SOURCE_DIR: Final[str] = "src"
        self._TECH_DIR: Final[str] = "technologies"
        self._FULL_TECH_DIR: Final[pathlib.Path] = pathlib.Path(self._SOURCE_DIR).joinpath(self._TECH_DIR)
        self._SCHEMA_FILE: Final[pathlib.Path] = pathlib.Path("schema.json")

    def validate(self) -> None:
        if not self._SCHEMA_FILE.is_file():
            raise FileNotFoundError(f"Schema file '{self._SCHEMA_FILE}' not found!")
        with self._SCHEMA_FILE.open("r", encoding="utf8") as f:
            schema: dict = json.load(f)
        for tech_file in sorted(self._FULL_TECH_DIR.iterdir()):
            if not tech_file.name.endswith(".json"):
                continue
            with tech_file.open("r", encoding="utf8") as f:
                technologies: dict = json.load(f)
            try:
                validate(instance=technologies, schema=schema)
            except ValidationError as e:
                path: str = " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
                raise SchemaValidationException(f"{tech_file.name}: {e.message} (at {path})")


if __name__ == '__main__':
    SchemaValidator().validate()
