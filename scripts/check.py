import os
import pathlib
import subprocess
import sys
from typing import Final


class Checker:
    def __init__(self):
        self._VALIDATORS_DIR: Final[pathlib.Path] = pathlib.Path(".github").joinpath("workflows").joinpath("scripts")

    def check(self) -> bool:
        # runs every validator the CI runs, pr_validator compares with BASE_REF (origin/main by default)
        env: dict[str, str] = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        failed: list[str] = []
        for validator in sorted(self._VALIDATORS_DIR.glob("*_validator.py")):
            print(f"== {validator.stem}", flush=True)
            if subprocess.run([sys.executable, str(validator)], env=env).returncode != 0:
                failed.append(validator.stem)
        print(f"failed: {', '.join(failed)}" if failed else "all checks passed")
        return not failed


if __name__ == '__main__':
    if not Checker().check():
        raise SystemExit(1)
