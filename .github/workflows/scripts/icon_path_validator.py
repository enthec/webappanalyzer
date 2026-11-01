import json
import pathlib
import string
from collections import defaultdict
from typing import Final, Optional
from xml.etree import ElementTree

from PIL import Image


class InvalidStructureException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidSVGException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidImageException(Exception):
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

        # Detect case-insensitive filename collisions (problematic on
        # case-insensitive filesystems such as the default macOS/Windows volumes).
        by_lower: dict[str, list[str]] = defaultdict(list)
        for file in self._FULL_IMAGES_DIR.iterdir():
            if not file.is_file():
                continue
            by_lower[file.name.lower()].append(file.name)
            if file.name not in json_icons:
                raise InvalidStructureException(f"{file.name} must be used, {file} isn't used!")
            if file.suffix.lower() == ".svg":
                self._validate_svg(file)
            else:
                self._validate_raster(file)

        duplicates = {k: v for k, v in by_lower.items() if len(v) > 1}
        if duplicates:
            msgs = [
                f"{lower}: {', '.join(sorted(names))}"
                for lower, names in sorted(duplicates.items())
            ]
            raise InvalidStructureException(
                "Case-insensitive duplicate icon filenames found "
                "(problematic on case-insensitive filesystems):\n  "
                + "\n  ".join(msgs)
            )

    def _validate_svg(self, file: pathlib.Path) -> None:
        try:
            with file.open("r", encoding="utf8") as f:
                content: str = f.read()
            root: ElementTree.Element = ElementTree.fromstring(content)
        except ElementTree.ParseError as e:
            raise InvalidSVGException(f"Invalid SVG '{file.name}': {e}")
        # icons must be static images, no active content
        for element in root.iter():
            if element.tag.split("}")[-1].lower() == "script":
                raise InvalidSVGException(f"SVG '{file.name}' can't contain <script> elements")
            for attr_name, attr_value in element.attrib.items():
                local_name: str = attr_name.split("}")[-1].lower()
                if local_name.startswith("on"):
                    raise InvalidSVGException(f"SVG '{file.name}' can't contain event handlers ('{local_name}')")
                if local_name == "href" and attr_value.strip().lower().startswith("javascript:"):
                    raise InvalidSVGException(f"SVG '{file.name}' can't contain javascript: links")

    @staticmethod
    def _validate_raster(file: pathlib.Path) -> None:
        try:
            with Image.open(file) as image:
                image_format: Optional[str] = image.format
                image.verify()
        except Exception as e:
            raise InvalidImageException(f"'{file.name}' is not a valid image: {e}")
        # the format Pillow registers for this extension (.png -> PNG, .jpg -> JPEG)
        expected_format: Optional[str] = Image.registered_extensions().get(file.suffix.lower())
        if image_format != expected_format:
            raise InvalidImageException(f"'{file.name}' is a {image_format} image, its extension says {expected_format}")

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
