import pathlib
import string
from typing import Final


class DirNotFoundException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class FileNotFoundException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidStructureException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class StructureValidator:
    def __init__(self):
        self._SOURCE_DIR: Final[str] = "src"
        self._TECH_DIR: Final[str] = "technologies"
        self._FULL_TECH_DIR: Final[pathlib.Path] = pathlib.Path(self._SOURCE_DIR).joinpath(self._TECH_DIR)
        self._IMAGES_DIR: Final[str] = "images"
        self._ICONS_DIR: Final[str] = "icons"
        self._FULL_IMAGES_DIR: Final[pathlib.Path] = pathlib.Path(self._SOURCE_DIR).joinpath(self._IMAGES_DIR).joinpath(self._ICONS_DIR)

    def validate(self) -> None:
        if not pathlib.Path(self._SOURCE_DIR).is_dir():
            raise DirNotFoundException(f"{self._TECH_DIR} is not a valid directory")
        if not self._FULL_TECH_DIR.is_dir():
            raise DirNotFoundException(f"{self._FULL_TECH_DIR} is not a valid directory")
        if not self._FULL_IMAGES_DIR.is_dir():
            raise DirNotFoundException(f"{self._FULL_IMAGES_DIR} is not a valid directory")
        if not (path := pathlib.Path(self._SOURCE_DIR).joinpath("categories.json")).is_file():
            raise FileNotFoundException(f"{path} not found!")
        if not (path := pathlib.Path(self._SOURCE_DIR).joinpath("groups.json")).is_file():
            raise FileNotFoundException(f"{path} not found!")
        for file in self._FULL_TECH_DIR.iterdir():
            if file.is_dir():
                raise InvalidStructureException(f"{self._FULL_TECH_DIR} can only contain json files, {file} is invalid!")
            file_name: str = file.name
            if not file_name.endswith(".json"):
                raise InvalidStructureException(f"{file_name} in {self._FULL_TECH_DIR} must be .json")
            name: str = file_name.removesuffix(".json")
            if len(name) != 1:
                raise InvalidStructureException(f"{file_name} is not a valid name! must be 'one char' only")
            if name not in list(string.ascii_lowercase + "_"):
                raise InvalidStructureException(f"{file_name} is not a valid name! must be from [a to z] or _")
        for file in self._FULL_IMAGES_DIR.iterdir():
            if file.is_dir():
                raise InvalidStructureException(f"{self._FULL_IMAGES_DIR} can only contain images, {file} is invalid!")
            file_extension: str = file.name.split(".")[-1].lower()
            if file_extension not in ("svg", "png", "jpg", "jpeg"):
                raise InvalidStructureException(f"{self._FULL_IMAGES_DIR} can only contain image formatted files, {file} is invalid!")


if __name__ == '__main__':
    StructureValidator().validate()
