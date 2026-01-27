import json
import pathlib
from typing import Final, Any


class DuplicateKeyException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class OrderingException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidStructureException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class OrderValidator:
    def __init__(self):
        self._SOURCE_DIR: Final[str] = "src"
        self._TECH_DIR: Final[str] = "technologies"
        self._FULL_TECH_DIR: Final[pathlib.Path] = pathlib.Path(self._SOURCE_DIR).joinpath(self._TECH_DIR)

    def validate(self) -> None:
        if not self._FULL_TECH_DIR.is_dir():
            raise InvalidStructureException(f"{self._FULL_TECH_DIR} is not a valid directory")
        for tech_file in sorted(self._FULL_TECH_DIR.iterdir()):
            if not tech_file.name.endswith(".json"):
                continue
            self._check_ordering(tech_file)

    def _check_ordering(self, tech_file: pathlib.Path) -> None:
        with tech_file.open("r", encoding="utf8") as f:
            data: dict = json.load(f, object_pairs_hook=self._duplicate_key_validator)
        if not isinstance(data, dict):
            raise InvalidStructureException(f"{tech_file.name} root must be an object")
        keys: list[str] = list(data.keys())
        sorted_keys: list[str] = sorted(keys, key=lambda x: x.lower())
        if keys != sorted_keys:
            mismatches: list[str] = [
                f"Found '{actual}' expected '{expected}'"
                for actual, expected in zip(keys, sorted_keys)
                if actual != expected
            ]
            raise OrderingException(
                f"{tech_file.name} entries are not ordered alphabetically by keys:\n  " +
                "\n  ".join(mismatches)
            )

    @classmethod
    def _duplicate_key_validator(cls, pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateKeyException(f"Duplicate key found: '{key}'")
            result[key] = value
        return result


if __name__ == '__main__':
    OrderValidator().validate()
