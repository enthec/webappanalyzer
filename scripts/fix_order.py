import json
import pathlib
from typing import Final, Any


class DuplicateKeyException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class OrderFixer:
    def __init__(self):
        self._SOURCE_DIR: Final[str] = "src"
        self._TECH_DIR: Final[str] = "technologies"
        self._FULL_TECH_DIR: Final[pathlib.Path] = pathlib.Path(self._SOURCE_DIR).joinpath(self._TECH_DIR)

    def fix(self) -> None:
        for tech_file in sorted(self._FULL_TECH_DIR.iterdir()):
            if not tech_file.name.endswith(".json"):
                continue
            with tech_file.open("r", encoding="utf8") as f:
                data: dict = json.load(f, object_pairs_hook=self._duplicate_key_validator)
            sorted_data: dict[str, Any] = {
                key: data[key] for key in sorted(data.keys(), key=lambda x: x.lower())
            }
            with tech_file.open("w", encoding="utf8") as f:
                json.dump(sorted_data, f, indent=2, ensure_ascii=False)
                f.write("\n")

    @classmethod
    def _duplicate_key_validator(cls, pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateKeyException(f"Duplicate key found: '{key}'")
            result[key] = value
        return result


if __name__ == '__main__':
    OrderFixer().fix()
