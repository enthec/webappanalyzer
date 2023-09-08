import json
import pathlib
from typing import Final, Any


class FileNotFoundException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class MissingRequiredFieldException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidTypeException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidFormatException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class UnknownFieldsException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class CategoryValidator:
    def __init__(self):
        self._SOURCE_DIR: Final[str] = "src"
        self._GROUPS_FILE: Final[str] = "groups.json"
        self._FULL_GROUPS_PATH: Final[pathlib.Path] = pathlib.Path(self._SOURCE_DIR).joinpath(self._GROUPS_FILE)

    def validate(self) -> None:
        if not self._FULL_GROUPS_PATH.is_file():
            raise FileNotFoundException(f"{self._FULL_GROUPS_PATH} not found!")
        with self._FULL_GROUPS_PATH.open("r") as groups:
            group_data: dict = json.loads(groups.read())
            for group, content in group_data.items():
                if not isinstance(group, str):
                    raise InvalidTypeException(f"Group '{group}' is '{type(group).__name__}', but 'str' is required")
                if not group.isnumeric():
                    raise InvalidFormatException(f"Group '{group}' is not a numeric string")
                value: Any = content.get("name")
                if value is None:
                    raise MissingRequiredFieldException(f"Field 'name' not found for group '{group}'")
                unknown_fields: list[str] = [k for k in content if k != "name"]
                if unknown_fields:
                    raise UnknownFieldsException(f"Group '{group}' has unknown fields: '{', '.join(unknown_fields)}'")
                self._name_validator(group, value)

    @staticmethod
    def _name_validator(group_name: str, value: Any) -> None:
        if not isinstance(value, str):
            raise InvalidTypeException(f"Category '{group_name}.name' is '{type(value).__name__}', but 'str' is required")


if __name__ == '__main__':
    CategoryValidator().validate()
