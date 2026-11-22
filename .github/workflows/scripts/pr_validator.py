import json
import os
import pathlib
import re
import string
import subprocess
import sys
from collections import defaultdict
from typing import Final, Any, Optional

from publicsuffixlist import PublicSuffixList

sys.dont_write_bytecode = True
from technology_validator import TechnologiesValidator  # noqa: E402


class GitException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class PullRequestValidator:
    """
    Checks that only apply to what a pull request changes, compared with the merge base of BASE_REF.
    Existing entries are not checked, so these rules can be stricter than the other validators.
    """

    def __init__(self, base_ref: str, allow_bulk: bool):
        self._SOURCE_DIR: Final[str] = "src"
        self._TECH_DIR: Final[str] = "technologies"
        self._FULL_TECH_DIR: Final[pathlib.Path] = pathlib.Path(self._SOURCE_DIR).joinpath(self._TECH_DIR)
        self._FULL_ICONS_DIR: Final[pathlib.Path] = pathlib.Path(self._SOURCE_DIR).joinpath("images").joinpath("icons")
        # a pull request above these limits needs the 'bulk-change' label
        self._MAX_ADDED: Final[int] = 10
        self._MAX_MODIFIED: Final[int] = 10
        self._MAX_DELETED: Final[int] = 3
        self._MAX_ICON_BYTES: Final[int] = 100_000
        self._MIN_JS_GLOBAL_LENGTH: Final[int] = 4
        self._MIN_COOKIE_LENGTH: Final[int] = 5
        self._MIN_NAME_LENGTH: Final[int] = 3
        self._MIN_SIMILAR_NAME_LENGTH: Final[int] = 5
        self._HOST: Final[re.Pattern] = re.compile(r"(?<![a-z0-9-])(?:[a-z0-9-]+\.)+[a-z0-9-]+")
        # a host written with escaped and/or unescaped dots, not preceded by a backslash (\w.com is not a host)
        self._RAW_HOST: Final[re.Pattern] = re.compile(r"(?<![\\a-z0-9-])(?:[a-z0-9-]+\\?\.)+[a-z0-9-]+", re.IGNORECASE)
        self._QUERY_STRING: Final[re.Pattern] = re.compile(r"(?<!\\)\?[a-z_]+=", re.IGNORECASE)
        self._ZERO_OR_MORE_SLASHES: Final[re.Pattern] = re.compile(r"(?<!\\)/\*")
        self._psl: Final[PublicSuffixList] = PublicSuffixList(accept_unknown=False)
        self._technologies: Final[TechnologiesValidator] = TechnologiesValidator()
        self._PATTERN_FIELDS: Final[list[str]] = self._technologies.get_pattern_fields()
        with pathlib.Path("schema.json").open("r", encoding="utf8") as f:
            tech_properties: dict = json.load(f)["additionalProperties"]["properties"]
        self._DEPRECATED_FIELDS: Final[list[str]] = [field for field, schema in tech_properties.items() if schema.get("deprecated")]
        self._allow_bulk: Final[bool] = allow_bulk
        self._base: Final[str] = self._git("merge-base", base_ref, "HEAD").strip()
        self._locations: Optional[dict[str, tuple[pathlib.Path, int]]] = None
        self._errors: int = 0
        self._warnings: int = 0

    def validate(self) -> bool:
        base_techs: dict[str, dict] = self._load_base_techs()
        head_techs: dict[str, dict] = self._technologies.get_technologies()
        added: list[str] = sorted(name for name in head_techs if name not in base_techs)
        deleted: list[str] = sorted(name for name in base_techs if name not in head_techs)
        modified: list[str] = sorted(name for name in head_techs if name in base_techs and head_techs[name] != base_techs[name])
        print(f"compared with {self._base[:10]}: {len(added)} added, {len(modified)} modified, {len(deleted)} deleted")

        self._check_scope(added, modified, deleted)
        owners: dict[str, dict[str, set[str]]] = self._owners(head_techs)
        for name in added:
            self._check_new_tech(name, head_techs[name], head_techs, owners)
        for name in modified:
            self._check_modified_tech(name, base_techs[name], head_techs[name])
        self._check_icons()
        print(f"{self._errors} errors, {self._warnings} warnings")
        return self._errors == 0

    def _check_scope(self, added: list[str], modified: list[str], deleted: list[str]) -> None:
        for name in deleted:
            self._report("warning", None, f"Tech '{name}' is deleted, make sure this is intended")
        if self._allow_bulk:
            return
        hint: str = "split the pull request or ask a maintainer for the 'bulk-change' label"
        if len(deleted) > self._MAX_DELETED:
            self._report("error", None, f"{len(deleted)} techs are deleted (max {self._MAX_DELETED}), was the file copied from an old version? {hint}")
        if len(modified) > self._MAX_MODIFIED:
            self._report("error", None, f"{len(modified)} techs are modified (max {self._MAX_MODIFIED}), {hint}")
        if len(added) > self._MAX_ADDED:
            self._report("error", None, f"{len(added)} techs are added (max {self._MAX_ADDED}), {hint}")

    def _check_new_tech(self, name: str, data: dict, techs: dict[str, dict], owners: dict[str, dict[str, set[str]]]) -> None:
        if not data.get("description"):
            self._report("error", name, f"Tech '{name}' needs a 'description'")
        if not data.get("icon"):
            self._report("error", name, f"Tech '{name}' needs an 'icon'")
        self._check_names(name, data, set(), set())
        self._check_deprecated(name, {}, data)
        for field, pattern in self._patterns(data):
            self._check_regex(name, field, pattern)
        self._check_specificity(name, data)
        self._check_overlap(name, data, techs, owners)

    def _check_modified_tech(self, name: str, old: dict, new: dict) -> None:
        old_patterns: set[tuple[str, str]] = set(self._patterns(old))
        for field, pattern in self._patterns(new):
            if (field, pattern) not in old_patterns:
                self._check_regex(name, field, pattern)
        self._check_names(name, new, set(old.get("js", {})), set(old.get("cookies", {})))
        self._check_deprecated(name, old, new)

    def _check_deprecated(self, name: str, old: dict, new: dict) -> None:
        # existing patterns in a deprecated field can be fixed, but the field can't get more patterns
        for field in self._DEPRECATED_FIELDS:
            old_count: int = len(self._strings(old.get(field)))
            new_count: int = len(self._strings(new.get(field)))
            if new_count > old_count:
                self._report("error", name, f"'{field}' is deprecated (see schema.json), '{name}' can't add patterns to it, use another field")

    def _check_names(self, name: str, data: dict, old_js: set[str], old_cookies: set[str]) -> None:
        for key in data.get("js", {}):
            root: str = key.split(".")[0].lstrip("_$")
            if key not in old_js and len(root) < self._MIN_JS_GLOBAL_LENGTH:
                self._report("error", name, f"js global '{key}' in '{name}' is too short to be specific (min {self._MIN_JS_GLOBAL_LENGTH} chars)")
        for cookie in data.get("cookies", {}):
            if cookie not in old_cookies and len(cookie.lstrip("_")) < self._MIN_COOKIE_LENGTH:
                self._report("error", name, f"cookie '{cookie}' in '{name}' is too short to be specific (min {self._MIN_COOKIE_LENGTH} chars)")

    def _check_regex(self, name: str, field: str, pattern: str) -> None:
        if field == "dom":
            return
        for match in self._RAW_HOST.finditer(pattern):
            host: str = match.group(0)
            if re.search(r"(?<!\\)\.", host) and self._psl.privatesuffix(host.replace("\\.", ".").lower()):
                self._report("error", name, f"{field} pattern '{pattern}' in '{name}' has an unescaped '.' in '{host}', use '\\.'")
                break
        if self._QUERY_STRING.search(pattern):
            self._report("error", name, f"{field} pattern '{pattern}' in '{name}' has an unescaped '?' before a query string, use '\\?'")
        if field == "html" and pattern.startswith("^") and pattern.endswith("$"):
            self._report("error", name, f"html pattern '{pattern}' in '{name}' is anchored with ^...$ but html is matched against the whole page")
        if self._ZERO_OR_MORE_SLASHES.search(pattern):
            self._report("warning", name, f"{field} pattern '{pattern}' in '{name}' has '/*', which means 'zero or more slashes', not a wildcard")

    def _check_specificity(self, name: str, data: dict) -> None:
        brand_tokens: set[str] = self._brand_tokens(name, data)
        for field, pattern in self._patterns(data):
            if not self._domains(pattern) and not self._has_brand(pattern, brand_tokens):
                self._report("warning", name, f"{field} pattern '{pattern}' in '{name}' contains neither a domain nor the brand name, make sure it can't match other sites")
        for key in list(data.get("js", {})) + list(data.get("cookies", {})):
            if not self._has_brand(key, brand_tokens):
                self._report("warning", name, f"'{key}' in '{name}' doesn't contain the brand name, make sure no other script uses it")

    def _check_overlap(self, name: str, data: dict, techs: dict[str, dict], owners: dict[str, dict[str, set[str]]]) -> None:
        for kind in ("js", "cookies"):
            for key in data.get(kind, {}):
                for other in sorted(owners[kind][key] - {name}):
                    self._report("error", name, f"{kind} '{key}' in '{name}' is already used by '{other}', is it the same technology?")
        for kind in ("meta", "headers"):
            for key, value in data.get(kind, {}).items():
                if literal := self._literal(value):
                    for other in sorted(owners[kind][f"{key.lower()}: {literal}"] - {name}):
                        self._report("warning", name, f"{kind} '{key}: {value}' in '{name}' is already used by '{other}', is it a duplicate?")
        for domain in sorted(self._tech_domains(data)):
            others: set[str] = owners["domains"][domain] - {name}
            # a domain used by a single other tech belongs to it, one used by several is a shared host (CDN, platform)
            if len(others) == 1:
                self._report("warning", name, f"'{domain}' is already used by '{next(iter(others))}', is it a duplicate?")
        own_name: str = self._normalize(name)
        for other in techs:
            other_name: str = self._normalize(other)
            shorter, longer = sorted((own_name, other_name), key=len)
            if other != name and len(shorter) >= self._MIN_SIMILAR_NAME_LENGTH and (longer.startswith(shorter) or longer.endswith(shorter)):
                self._report("warning", name, f"'{name}' has a similar name to '{other}', is it a duplicate?")

    def _check_icons(self) -> None:
        changed: set[str] = set(self._git("diff", "--name-only", "--diff-filter=AM", self._base, "--", self._FULL_ICONS_DIR.as_posix()).splitlines())
        changed.update(self._git("ls-files", "--others", "--exclude-standard", "--", self._FULL_ICONS_DIR.as_posix()).splitlines())
        for path in sorted(changed):
            icon: pathlib.Path = pathlib.Path(path)
            if icon.is_file() and icon.stat().st_size > self._MAX_ICON_BYTES:
                self._report("error", None, f"icon '{icon.name}' is {icon.stat().st_size // 1000} KB (max {self._MAX_ICON_BYTES // 1000} KB), optimize it", file=icon)

    def _patterns(self, data: dict) -> list[tuple[str, str]]:
        patterns: list[tuple[str, str]] = []
        for field in self._PATTERN_FIELDS:
            value: Any = data.get(field)
            if field == "dom" and isinstance(value, dict):
                patterns.extend((field, selector) for selector in value)
            patterns.extend((field, pattern) for pattern in self._strings(value))
        return [(field, pattern.split(r"\;")[0]) for field, pattern in patterns if pattern.split(r"\;")[0]]

    def _strings(self, value: Any) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [string_value for item in value for string_value in self._strings(item)]
        if isinstance(value, dict):
            return [string_value for item in value.values() for string_value in self._strings(item)]
        return []

    def _owners(self, techs: dict[str, dict]) -> dict[str, dict[str, set[str]]]:
        owners: dict[str, dict[str, set[str]]] = {kind: defaultdict(set) for kind in ("js", "cookies", "meta", "headers", "domains")}
        for name, data in techs.items():
            for kind in ("js", "cookies"):
                for key in data.get(kind, {}):
                    owners[kind][key].add(name)
            for kind in ("meta", "headers"):
                for key, value in data.get(kind, {}).items():
                    if literal := self._literal(value):
                        owners[kind][f"{key.lower()}: {literal}"].add(name)
            for domain in self._tech_domains(data):
                owners["domains"][domain].add(name)
        return owners

    def _tech_domains(self, data: dict) -> set[str]:
        return {domain for _, pattern in self._patterns(data) for domain in self._domains(pattern)}

    def _domains(self, pattern: str) -> set[str]:
        domains: set[str] = set()
        for host in self._HOST.findall(pattern.replace("\\.", ".").lower()):
            if registrable := self._psl.privatesuffix(host):
                domains.add(registrable)
        return domains

    def _brand_tokens(self, name: str, data: dict) -> set[str]:
        tokens: set[str] = {self._normalize(name)}
        tokens.update(self._normalize(word) for word in re.split(r"[\s._-]+", name))
        host: str = re.sub(r"^https?://", "", data.get("website", "")).split("/")[0].lower()
        registrable: str = self._psl.privatesuffix(host) or host
        public: str = self._psl.publicsuffix(host) or ""
        label: str = registrable.removesuffix(f".{public}") if public else registrable
        tokens.add(self._normalize(label))
        tokens.update(self._normalize(part) for part in label.split("-"))
        return {token for token in tokens if len(token) >= self._MIN_NAME_LENGTH}

    def _has_brand(self, text: str, brand_tokens: set[str]) -> bool:
        normalized: str = self._normalize(text)
        return any(token in normalized for token in brand_tokens)

    @staticmethod
    def _literal(pattern: str) -> Optional[str]:
        # the text a pattern matches when it has no regex syntax, '^eZ Platform$' -> 'ez platform'
        text: str = pattern.split(r"\;")[0].removeprefix("^").removesuffix("$")
        if not text or re.search(r"\\[a-zA-Z]", text) or any(char in text for char in "()[]{}*+?|."):
            return None
        return text.lower()

    @staticmethod
    def _normalize(text: str) -> str:
        return "".join(char for char in text.lower() if char in string.ascii_lowercase + string.digits)

    def _load_base_techs(self) -> dict[str, dict]:
        techs: dict[str, dict] = {}
        for tech_file in sorted(self._FULL_TECH_DIR.glob("*.json")):
            content: Optional[str] = self._git_optional("show", f"{self._base}:{tech_file.as_posix()}")
            if content:
                techs.update(json.loads(content))
        return techs

    def _report(self, level: str, tech: Optional[str], message: str, file: Optional[pathlib.Path] = None) -> None:
        line: int = 1
        if tech is not None:
            file, line = self._locate(tech)
        if level == "error":
            self._errors += 1
        else:
            self._warnings += 1
        if os.getenv("GITHUB_ACTIONS") == "true":
            print(f"::{level} {f'file={file},line={line}' if file else ''}::{message}")
        else:
            print(f"{level.upper()} {f'{file}:{line}: ' if file else ''}{message}")

    def _locate(self, tech: str) -> tuple[pathlib.Path, int]:
        if self._locations is None:
            # tech keys are the only lines indented with 2 spaces that open an object
            self._locations = {}
            for tech_file in sorted(self._FULL_TECH_DIR.glob("*.json")):
                with tech_file.open("r", encoding="utf8") as f:
                    for number, line in enumerate(f, start=1):
                        if line.startswith('  "') and line.rstrip("\n").endswith(": {"):
                            self._locations[json.loads(line.strip().removesuffix(": {"))] = (tech_file, number)
        return self._locations.get(tech, (self._FULL_TECH_DIR, 1))

    @staticmethod
    def _git(*args: str) -> str:
        result: subprocess.CompletedProcess = subprocess.run(["git", *args], capture_output=True, text=True)
        if result.returncode != 0:
            raise GitException(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout

    @staticmethod
    def _git_optional(*args: str) -> Optional[str]:
        result: subprocess.CompletedProcess = subprocess.run(["git", *args], capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else None


if __name__ == '__main__':
    validator: PullRequestValidator = PullRequestValidator(
        os.getenv("BASE_REF", "origin/main"),
        os.getenv("ALLOW_BULK", "false").lower() == "true"
    )
    if not validator.validate():
        raise SystemExit(1)
