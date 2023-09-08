import json
import pathlib
from typing import Final, Any, Callable, Optional


class FileNotFoundException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class GroupNotFoundException(Exception):
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
        self._CATEGORIES_FILE: Final[str] = "categories.json"
        self._GROUPS_FILE: Final[str] = "groups.json"
        self._FULL_CATEGORIES_PATH: Final[pathlib.Path] = pathlib.Path(self._SOURCE_DIR).joinpath(self._CATEGORIES_FILE)
        self._FULL_GROUPS_PATH: Final[pathlib.Path] = pathlib.Path(self._SOURCE_DIR).joinpath(self._GROUPS_FILE)
        self._validators: dict[str, Callable] = {
            "groups": self._group_validator,
            "name": self._name_validator,
            "priority": self._priority_validator
        }
        self._groups: Optional[dict] = None

    def validate(self) -> None:
        if not self._FULL_CATEGORIES_PATH.is_file():
            raise FileNotFoundException(f"{self._FULL_CATEGORIES_PATH} not found!")
        if not self._FULL_GROUPS_PATH.is_file():
            raise FileNotFoundException(f"{self._FULL_GROUPS_PATH} not found!")
        with self._FULL_GROUPS_PATH.open("r") as groups:
            self._groups: Optional[dict] = json.loads(groups.read())
        with self._FULL_CATEGORIES_PATH.open("r") as categories:
            data: dict = json.loads(categories.read())
            for category, content in data.items():
                if not isinstance(category, str):
                    raise InvalidTypeException(f"Category '{category}' is '{type(category).__name__}', but 'str' is required")
                if not category.isnumeric():
                    raise InvalidFormatException(f"Category '{category}' is not a numeric string")
                for key, validator in self._validators.items():
                    value: Any = content.get(key)
                    if value is None:
                        raise MissingRequiredFieldException(f"Field '{key}' not found for category '{category}'")
                    validator(category, value)
                unknown_fields: list[str] = [k for k in content if k not in self._validators.keys()]
                if unknown_fields:
                    raise UnknownFieldsException(f"Category '{category}' has unknown fields: '{', '.join(unknown_fields)}'")

    def _group_validator(self, cat_name: str, value: Any) -> None:
        if not isinstance(value, list):
            raise InvalidTypeException(f"Category '{cat_name}.groups' is '{type(value).__name__}', but 'list' is required")
        for item in value:
            if not isinstance(item, int):
                raise InvalidTypeException(f"Category '{cat_name}.groups' has a '{type(item).__name__}' item, but 'int' is required")
            if str(item) not in self._groups.keys():
                raise GroupNotFoundException(f"Category '{cat_name}.groups.{item}' doesn't exist in the groups.json file")

    @staticmethod
    def _name_validator(cat_name: str, value: Any) -> None:
        if not isinstance(value, str):
            raise InvalidTypeException(f"Category '{cat_name}.name' is '{type(value).__name__}', but 'str' is required")

    @staticmethod
    def _priority_validator(cat_name: str, value: Any) -> None:
        if not isinstance(value, int):
            raise InvalidTypeException(f"Category '{cat_name}.priority' is '{type(value).__name__}', but 'int' is required")


if __name__ == '__main__':
    CategoryValidator().validate()
