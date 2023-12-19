import json
import pathlib
import string
from typing import Final


class InvalidStructureException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class IconValidator:
    def __init__(self):
        self._SOURCE_DIR: Final[str] = "src"
        self._TECH_DIR: Final[str] = "technologies"
        self._FULL_TECH_DIR: Final[pathlib.Path] = pathlib.Path(self._SOURCE_DIR).joinpath(self._TECH_DIR)
        self._IMAGES_DIR: Final[str] = "images"
        self._ICONS_DIR: Final[str] = "icons"
        self._FULL_IMAGES_DIR: Final[pathlib.Path] = pathlib.Path(self._SOURCE_DIR).joinpath(self._IMAGES_DIR).joinpath(self._ICONS_DIR)

    def validate(self) -> None:
        for file in self._FULL_IMAGES_DIR.iterdir():
            if not self.validate_icon(file.name):
                raise InvalidStructureException(f"{file.name} must be used, {file} isn't used!")

    def validate_icon(self, icon: str) -> bool:
        letters: list[str] = list(string.ascii_lowercase)
        letters.insert(0, '_')

        for letter in letters:
            icon_path: pathlib.Path = self._FULL_TECH_DIR.joinpath(f"{letter}.json")
            with icon_path.open("r", encoding="utf8") as json_file:
                technologies: dict = json.load(json_file)

            for tech, data in technologies.items():
                for key, value in data.items():
                    if 'icon' == key:
                        if icon == data['icon']:
                            return True
                        else:
                            break
        return False


if __name__ == '__main__':
    IconValidator().validate()
