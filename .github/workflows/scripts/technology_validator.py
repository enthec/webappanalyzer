import json
import os
import pathlib
from typing import Final, Any, Type


class MissingRequiredFieldException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidTypeForFieldException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class UnknownFieldsException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class AbstractValidator:
    def __init__(self, required: bool = False):
        self._required = required

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


class TechnologiesValidator:
    def __init__(self, file_name: str):
        super().__init__()
        self._SOURCE_DIR: Final[str] = "src"
        self._TECH_DIR: Final[str] = "technologies"
        self._FULL_TECH_DIR: Final[pathlib.Path] = pathlib.Path(self._SOURCE_DIR).joinpath(self._TECH_DIR)
        self._TECH_FILE: Final[pathlib.Path] = self._FULL_TECH_DIR.joinpath(file_name)
        self._validators: dict[str, AbstractValidator] = {  # TODO confidence and version validator
            "cats": ArrayValidator(True),
            "website": StringValidator(True),
            "description": StringValidator(),
            "icon": StringValidator(),
            "cpe": StringValidator(),  # TODO cpe regex
            "saas": BoolValidator(),
            "oss": BoolValidator(),
            "pricing": ArrayValidator(),
            "implies": StringOrArrayValidator(),  # TODO cat validation
            "requires": StringOrArrayValidator(),  # TODO ^
            "excludes": StringOrArrayValidator(),  # TODO ^
            "requiresCategory": IntOrArrayValidator(),  # TODO validate Cat exists
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
        with self._TECH_FILE.open("r") as f:
            technologies: dict = json.loads(f.read())
            for tech, data in technologies.items():
                p: TechnologyProcessor = TechnologyProcessor(tech, data, self._validators)
                p.process()


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
                raise InvalidTypeForFieldException(f"tech '{self._tech_name}' for field '{validator}' has an invalid type. '{'|'.join([t.__name__ for t in p.get_type()])}' is required, got type '{type(value).__name__}' -> '{value}'")
        unknown_fields: list[str] = [field for field in self._tech_data.keys() if field not in self._validators.keys()]
        if unknown_fields:
            raise UnknownFieldsException(f"tech '{self._tech_name}' has unknown fields: '{', '.join(unknown_fields)}'")


if __name__ == '__main__':
    TechnologiesValidator(os.getenv("TECH_FILE_NAME")).validate()
