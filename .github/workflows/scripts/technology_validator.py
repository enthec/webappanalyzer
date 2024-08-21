import abc
import json
import os
import pathlib
import re
import string
from typing import Final, Any, Type, Optional

from bs4 import BeautifulSoup


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


class InvalidKeyException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class ImageNotFoundException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidRegexException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class DuplicateTechnologyException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidTechFileException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidPriceException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidCPEException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class TooManyTagsException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidTagException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class AbstractValidator:
    def __init__(self, required: bool = False):
        self._required = required
        self._custom_error: Optional[Exception] = None
        self.__version_match = re.compile(r"^(?:(?P<prefix>.*)?\\(?P<group>\d+)(?:\?(?P<first>.*)?:(?P<second>.*)?)?|(?P<fixed>[a-zA-Z0-9.]+)?)$")

    def process(self, property_name: str, tech_name: str, data: Any) -> bool:
        if self._required and not data:
            raise MissingRequiredFieldException(f"'{property_name}' field is required for {tech_name}!")
        if data is None:
            return True
        return self._validate(tech_name, data)

    def _validate(self, tech_name: str, data: Any) -> bool:
        if isinstance(data, str):
            if not self._validate_tags(tech_name, data):
                return False
        for t in self.get_type():
            if isinstance(data, t):
                return True
        return False

    def _validate_tags(self, tech_name: str, pattern: str) -> bool:
        tags: list[str] = pattern.split(r"\;")[1:]
        if len(tags) > 2:
            self._set_custom_error(TooManyTagsException(f"pattern '{pattern}' for tech '{tech_name}' has more than 2 tags, only confidence & version are allowed!"))
            return False
        tag_names: list[str] = [tag.split(":")[0].lower() for tag in tags]
        if len(tag_names) == 2 and tag_names[0] == tag_names[1]:
            self._set_custom_error(TooManyTagsException(f"pattern '{pattern}' for tech '{tech_name}' has more than 2 tags named {tag_names[1]}!"))
            return False
        for tag_name, tag_value in {tag.split(":")[0]: ":".join(tag.split(":")[1:]) for tag in tags}.items():
            if tag_name == "confidence":
                if not tag_value.isnumeric():
                    self._set_custom_error(InvalidTagException(f"Invalid tag value '{tag_value}' for tech '{tech_name}' in pattern '{pattern}', confidence must be numeric!"))
                    return False
                if 0 >= int(tag_value) >= 100:
                    self._set_custom_error(InvalidTagException(f"Invalid tag value '{tag_value}' for tech '{tech_name}' in pattern '{pattern}', confidence must be between 0 and 100!"))
                    return False
            elif tag_name == "version":
                match: re.Match = self.__version_match.match(tag_value)
                if not match:
                    self._set_custom_error(InvalidTagException(f"Invalid tag value '{tag_value}' for tech '{tech_name}' in pattern '{pattern}', version is invalid!"))
                    return False
            else:
                self._set_custom_error(InvalidTagException(f"this tag '{tag_name}' for tech '{tech_name}' in pattern '{pattern}' doesn't exist!"))
                return False
        return True

    def get_type(self) -> list[Type]:
        raise NotImplementedError()

    def get_custom_error(self) -> Optional[Exception]:
        return self._custom_error

    def _set_custom_error(self, custom_error: Exception) -> None:
        self._custom_error = custom_error


class PricingValidator(AbstractValidator):
    def _validate(self, tech_name: str, data: Any) -> bool:
        if not super()._validate(tech_name, data):
            return False
        for price in data:
            if price not in ("low", "mid", "high", "freemium", "poa", "payg", "onetime", "recurring"):
                self._set_custom_error(InvalidPriceException(f"Pricing '{price}' for tech '{tech_name}' is not valid"))
                return False
        return True

    def get_type(self) -> list[Type]:
        return [list]


class RegexValidator(abc.ABC, AbstractValidator):
    def __init__(self, contains_regex: bool = False):
        super().__init__()
        self._contains_regex = contains_regex

    def _validate(self, tech_name: str, data: Any) -> bool:
        if not super()._validate(tech_name, data):
            return False
        if self._contains_regex:
            if not self._validate_regex(tech_name, data):
                return False
        return True

    def _validate_regex(self, tech_name: str, data: Any) -> bool:
        if isinstance(data, str):
            try:
                if not self._validate_tags(tech_name, data):
                    return False
                re.compile(data.split(r"\;")[0])
            except re.error as e:
                self._set_custom_error(InvalidRegexException(f"Unable to compile regex '{data}' for tech '{tech_name}', got error: {e.msg}"))
                return False
        elif isinstance(data, dict):
            for _, val in data.items():
                if not self._validate_regex(tech_name, val):
                    return False
        elif isinstance(data, list):
            for item in data:
                if not self._validate_regex(tech_name, item):
                    return False
        return True


class StringValidator(AbstractValidator):
    def get_type(self) -> list[Type]:
        return [str]


class BoolValidator(AbstractValidator):
    def get_type(self) -> list[Type]:
        return [bool]


class ArrayValidator(RegexValidator):
    def get_type(self) -> list[Type]:
        return [list]


class DictValidator(RegexValidator):
    def get_type(self) -> list[Type]:
        return [dict]


class CategoryValidator(ArrayValidator):
    def __init__(self, categories: list[int], required: bool = False):
        super().__init__(required)
        self._categories: Final[list[int]] = categories

    def _validate(self, tech_name: str, data: Any) -> bool:
        if not super()._validate(tech_name, data):
            return False
        for category_id in data:
            if category_id not in self._categories:
                self._set_custom_error(CategoryNotFoundException(f"The category '{category_id}' for tech '{tech_name}' does not exist!"))
                return False
        return True


class DomValidator(RegexValidator):
    def _validate(self, tech_name: str, data: Any) -> bool:
        if isinstance(data, list):
            for element in data:
                if not self._validate_tags(tech_name, element):
                    return False
                BeautifulSoup("", "html.parser").select(element.split(r"\;")[0])
        elif isinstance(data, dict):
            for k, v in data.items():
                BeautifulSoup("", "html.parser").select(k)
                if isinstance(v, dict):
                    for key, val in v.items():
                        if key in ("attributes", "properties"):
                            if isinstance(val, dict):
                                for attr_name, attr_val in val.items():
                                    if not isinstance(attr_name, str):
                                        self._set_custom_error(InvalidTypeForFieldException(f"Invalid type for dom in tech '{tech_name}', selector '{k}' '{key}' key must be string!"))
                                        return False
                                    if not isinstance(attr_val, str):
                                        self._set_custom_error(InvalidTypeForFieldException(f"Invalid type for dom in tech '{tech_name}', selector '{k}' '{key}' value must be string!"))
                                        return False
                                    if not self._validate_regex(tech_name, attr_val):
                                        return False
                            else:
                                self._set_custom_error(InvalidTypeForFieldException(f"Invalid type for dom in tech '{tech_name}', selector '{k}' object is required inside '{key}' but {type(val).__name__} was found!"))
                                return False
                        elif key == "text":
                            if isinstance(val, str):
                                if not self._validate_regex(tech_name, val):
                                    return False
                        elif key == "exists":
                            if val.split(r"\;")[0] != "":
                                if not self._validate_tags(tech_name, val):
                                    return False
                                self._set_custom_error(InvalidTypeForFieldException(f"Invalid value for dom in tech '{tech_name}', selector '{k}' empty string is required inside '{key}' but {val} was found!"))
                                return False
                        else:
                            self._set_custom_error(UnknownFieldsException(f"Invalid key for tech '{tech_name}' (attributes, text, properties, exists) are required but '{key}' was found inside of the {k} selector!"))
                            return False
                else:
                    self._set_custom_error(InvalidTypeForFieldException(f"Invalid type for dom in tech '{tech_name}' object is required inside the selector!"))
                    return False
        else:
            return False
        return True

    def get_type(self) -> list[Type]:
        return [list, dict]


class IconValidator(StringValidator):
    def __init__(self, icons: list[str], required: bool = False):
        super().__init__(required)
        self._icons: Final[list[str]] = icons

    def _validate(self, tech_name: str, data: Any) -> bool:
        if not super()._validate(tech_name, data):
            return False
        if data not in self._icons:
            self._set_custom_error(ImageNotFoundException(f"The image '{data}' for tech '{tech_name}' does not exist!"))
            return False
        return True


class CPEValidator(StringValidator):
    def __init__(self):
        super().__init__()

    def _validate(self, tech_name: str, data: Any) -> bool:
        if not super()._validate(tech_name, data):
            return False
        # https://csrc.nist.gov/schema/cpe/2.3/cpe-naming_2.3.xsd
        cpe_regex: str = r"""cpe:2\.3:[aho\*\-](:(((\?*|\*?)([a-zA-Z0-9\-\._]|(\\[\\\*\?!"#$$%&'\(\)\+,/:;<=>@\[
        \]\^`\{\|}~]))+(\?*|\*?))|[\*\-])){5}(:(([a-zA-Z]{2,3}(-([a-zA-Z]{2}|[0-9]{3}))?)|[\*\-]))(:(((\?*|\*?)([
        a-zA-Z0-9\-\._]|(\\[\\\*\?!"#$$%&'\(\)\+,/:;<=>@\[\]\^`\{\|}~]))+(\?*|\*?))|[\*\-])){4}"""
        pattern: re.Pattern = re.compile(cpe_regex)
        if not pattern.match(data):
            self._set_custom_error(InvalidCPEException(f"The cpe {data} for tech '{tech_name}' is invalid!"))
            return False
        return True


class TechnologiesValidator:
    def __init__(self, file_name: str):
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
            "cpe": CPEValidator(),
            "saas": BoolValidator(),
            "oss": BoolValidator(),
            "pricing": PricingValidator(),
            "implies": ArrayValidator(),  # TODO cat validation
            "requires": ArrayValidator(),  # TODO ^
            "excludes": ArrayValidator(),  # TODO ^
            "requiresCategory": CategoryValidator(self._CATEGORIES),
            "cookies": DictValidator(contains_regex=True),
            "dom": DomValidator(),
            "dns": DictValidator(contains_regex=True),
            "js": DictValidator(contains_regex=True),
            "headers": DictValidator(contains_regex=True),
            "text": ArrayValidator(contains_regex=True),
            "css": ArrayValidator(contains_regex=True),
            "probe": DictValidator(),
            "robots": ArrayValidator(),
            "url": ArrayValidator(contains_regex=True),
            "xhr": ArrayValidator(contains_regex=True),
            "meta": DictValidator(contains_regex=True),
            "scriptSrc": ArrayValidator(contains_regex=True),
            "scripts": ArrayValidator(contains_regex=True),
            "html": ArrayValidator(contains_regex=True),
            "certIssuer": StringValidator()
        }

    def validate(self) -> None:
        initial_letter: str = self._TECH_FILE.name.removesuffix(".json")
        with self._TECH_FILE.open("r", encoding="utf8") as f:
            technologies: dict = json.loads(f.read(), object_pairs_hook=self._duplicate_key_validator)
            for tech, data in technologies.items():
                first: str = tech[0].lower()
                if initial_letter == "_":
                    if first in string.ascii_lowercase:
                        raise InvalidTechFileException(f"Tech '{tech}' starts with the letter '{first}', it should not be located in the '{self._TECH_FILE.name}' file, but '{first}.json'")
                elif first != initial_letter:
                    suggested_file: str = f"{first}.json" if first in string.ascii_lowercase else "_.json"
                    raise InvalidTechFileException(f"Tech '{tech}' does not start with '{initial_letter}', it should not be located in the '{self._TECH_FILE.name}' file, but '{suggested_file}'")
                if tech.strip() != tech:
                    raise InvalidTechFileException(f"Tech '{tech}' can't start or end with whitespace ' '")
                p: TechnologyProcessor = TechnologyProcessor(tech, data, self._validators)
                p.process()

    @classmethod
    def _duplicate_key_validator(cls, pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
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
