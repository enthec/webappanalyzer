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
        json_icons: set[str] = self.get_json_icons()
        for file in self._FULL_IMAGES_DIR.iterdir():
            if file.name not in json_icons:
                raise InvalidStructureException(f"{file.name} must be used, {file} isn't used!")

    def get_json_icons(self) -> set[str]:
        letters: list[str] = list(string.ascii_lowercase)
        letters.insert(0, '_')
        json_icons: set[str] = set()

        for letter in letters:
            icon_path: pathlib.Path = self._FULL_TECH_DIR.joinpath(f"{letter}.json")
            with icon_path.open("r", encoding="utf8") as json_file:
                technologies: dict = json.load(json_file)
            for tech, data in technologies.items():
                if value := data.get("icon"):
                    json_icons.add(value)
        return json_icons


if __name__ == '__main__':
    IconValidator().validate()
