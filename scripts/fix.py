import json
import pathlib
from typing import Any, Callable


class StructureFix:
    def __init__(self):
        self._src_path: pathlib.Path = pathlib.Path("src")
        self._transform: dict[str, Callable[[str | int], list]] = {
            "html": self._fix_to_list,
            "text": self._fix_to_list,
            "css": self._fix_to_list,
            "excludes": self._fix_to_list,
            "implies": self._fix_to_list,
            "requires": self._fix_to_list,
            "requiresCategory": self._fix_to_list,
            "scriptSrc": self._fix_to_list,
            "scripts": self._fix_to_list,
            "url": self._fix_to_list,
            "xhr": self._fix_to_list,
            "robots": self._fix_to_list,
            "dom": self._fix_to_list
        }

    @staticmethod
    def _fix_to_list(current_detector) -> list:
        if isinstance(current_detector, str) or isinstance(current_detector, int):
            return [current_detector]
        return current_detector

    @staticmethod
    def _do_nothing(current_detector):
        return current_detector

    def fix(self):
        for file in self._src_path.joinpath("technologies").iterdir():
            if not file.name.endswith(".json"):
                continue
            with file.open("r") as f:
                techs: dict[str, dict[str, Any]] = json.loads(f.read())
            for tech_name, tech_detectors in techs.copy().items():
                for detector_name, detector in tech_detectors.copy().items():
                    tech_detectors[detector_name] = self._transform.get(detector_name, self._do_nothing)(detector)
                techs[tech_name.strip()] = tech_detectors
            with file.open("w") as f:
                f.write(json.dumps(techs, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == '__main__':
    StructureFix().fix()
