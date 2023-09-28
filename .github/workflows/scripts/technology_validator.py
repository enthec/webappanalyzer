import json
import os
import pathlib
from typing import Final, Any, Type, Optional


class MissingRequiredFieldException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidTypeForFieldException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class UnknownFieldsException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class CategoryNotFoundException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class ImageNotFoundException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class DuplicateTechnologyException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class AbstractValidator:
    def __init__(self, required: bool = False):
        self._required = required
        self._custom_error: Optional[Exception] = None

    def process(self, property_name: str, tech_name: str, data: Any) -> bool:
        if self._required and not data:
            raise MissingRequiredFieldException(f"'{property_name}' field is required for {tech_name}!")
        if data is None:
            return True
        return self._validate(data)

    def _validate(self, data: Any) -> bool:
        for t in self.get_type():
            if isinstance(data, t):
                return True
        return False

    def get_type(self) -> list[Type]:
        raise NotImplementedError()

    def get_custom_error(self) -> Optional[Exception]:
        return self._custom_error

    def _set_custom_error(self, custom_error: Exception) -> None:
        self._custom_error = custom_error


class StringValidator(AbstractValidator):
    def get_type(self) -> list[Type]:
        return [str]


class ArrayValidator(AbstractValidator):
    def get_type(self) -> list[Type]:
        return [list]


class BoolValidator(AbstractValidator):
    def get_type(self) -> list[Type]:
        return [bool]


class StringOrArrayValidator(AbstractValidator):
    def get_type(self) -> list[Type]:
        return [str, list]


class StringOrArrayOrDictValidator(AbstractValidator):
    def get_type(self) -> list[Type]:
        return [str, list, dict]


class IntOrArrayValidator(AbstractValidator):
    def get_type(self) -> list[Type]:
        return [int, list]


class DictValidator(AbstractValidator):
    def get_type(self) -> list[Type]:
        return [dict]


class CategoryValidator(IntOrArrayValidator):
    def __init__(self, categories: list[int], required: bool = False):
        super().__init__(required)
        self._categories: Final[list[int]] = categories

    def _validate(self, data: Any) -> bool:
        type_validator: bool = super()._validate(data)
        if not type_validator:
            return False
        if isinstance(data, int):
            data = [data]
        for category_id in data:
            if category_id not in self._categories:
                self._set_custom_error(CategoryNotFoundException(f"The category '{category_id}' does not exist!"))
                return False
        return True


class IconValidator(StringValidator):
    def __init__(self, icons: list[str], required: bool = False):
        super().__init__(required)
        self._icons: Final[list[str]] = icons

    def _validate(self, data: Any) -> bool:
        type_validator: bool = super()._validate(data)
        if not type_validator:
            return False
        contains: bool = data in self._icons
        if not contains:
            self._set_custom_error(ImageNotFoundException(f"The image '{data}' does not exist!"))
            return False
        return True


class TechnologiesValidator:
    def __init__(self, file_name: str):
        super().__init__()
        self._SOURCE_DIR: Final[str] = "src"
        self._TECH_DIR: Final[str] = "technologies"
        self._FULL_TECH_DIR: Final[pathlib.Path] = pathlib.Path(self._SOURCE_DIR).joinpath(self._TECH_DIR)
        self._TECH_FILE: Final[pathlib.Path] = self._FULL_TECH_DIR.joinpath(file_name)
        with pathlib.Path(self._SOURCE_DIR).joinpath("categories.json").open("r", encoding="utf8") as categories:
            self._CATEGORIES: Final[list[int]] = [int(cat) for cat in json.loads(categories.read())]
        self._IMAGES_DIR: Final[str] = "images"
        self._ICONS_DIR: Final[str] = "icons"
        self._ICONS: Final[list[str]] = [icon.name for icon in pathlib.Path(self._SOURCE_DIR).joinpath(self._IMAGES_DIR).joinpath(self._ICONS_DIR).iterdir()]
        self._validators: dict[str, AbstractValidator] = {  # TODO confidence and version validator
            "cats": CategoryValidator(self._CATEGORIES, True),
            "website": StringValidator(True),
            "description": StringValidator(),
            "icon": IconValidator(self._ICONS),
            "cpe": StringValidator(),  # TODO cpe regex
            "saas": BoolValidator(),
            "oss": BoolValidator(),
            "pricing": ArrayValidator(),
            "implies": StringOrArrayValidator(),  # TODO cat validation
            "requires": StringOrArrayValidator(),  # TODO ^
            "excludes": StringOrArrayValidator(),  # TODO ^
            "requiresCategory": CategoryValidator(self._CATEGORIES),
            "cookies": DictValidator(),
            "dom": StringOrArrayOrDictValidator(),
            "dns": DictValidator(),
            "js": DictValidator(),
            "headers": DictValidator(),
            "text": StringOrArrayValidator(),
            "css": StringOrArrayValidator(),
            "probe": DictValidator(),
            "robots": StringOrArrayValidator(),
            "url": StringOrArrayValidator(),
            "xhr": StringOrArrayValidator(),
            "meta": DictValidator(),
            "scriptSrc": StringOrArrayValidator(),
            "scripts": StringOrArrayValidator(),
            "html": StringOrArrayValidator(),
            "certIssuer": StringValidator()
        }

    def validate(self) -> None:
        with self._TECH_FILE.open("r", encoding="utf8") as f:
            technologies: dict = json.loads(f.read(), object_pairs_hook=self._duplicate_key_validator)
            for tech, data in technologies.items():
                p: TechnologyProcessor = TechnologyProcessor(tech, data, self._validators)
                p.process()

    @classmethod
    def _duplicate_key_validator(cls, pairs) -> dict:
        result: dict = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateTechnologyException(f"Tech '{key}' is duplicated!")
            result[key] = value
        return result


class TechnologyProcessor:
    def __init__(self, tech_name: str, tech_data: dict, validators: dict[str, AbstractValidator]):
        self._tech_name: str = tech_name
        self._tech_data: dict = tech_data
        self._validators: dict[str, AbstractValidator] = validators

    def process(self) -> None:
        for validator, p in self._validators.items():
            value: Any = self._tech_data.get(validator)
            valid: bool = p.process(validator, self._tech_name, value)
            if not valid:
                if not p.get_custom_error():
                    raise InvalidTypeForFieldException(f"field '{validator}' for tech '{self._tech_name}' has an invalid type. '{'|'.join([t.__name__ for t in p.get_type()])}' is required, got type '{type(value).__name__}' -> '{value}'")
                else:
                    raise p.get_custom_error()
        unknown_fields: list[str] = [field for field in self._tech_data.keys() if field not in self._validators.keys()]
        if unknown_fields:
            raise UnknownFieldsException(f"tech '{self._tech_name}' has unknown fields: '{', '.join(unknown_fields)}'")


if __name__ == '__main__':
    # for letter in string.ascii_lowercase + "_":
    #     TechnologiesValidator(os.getenv("TECH_FILE_NAME", f"{letter}.json")).validate()
    TechnologiesValidator(os.getenv("TECH_FILE_NAME", f"a.json")).validate()
