import tomllib
from dataclasses import fields
from pathlib import Path

from reviewability.config.models import ReviewabilityConfig

_KNOWN_FIELDS: frozenset[str] = frozenset(f.name for f in fields(ReviewabilityConfig))


def parse_config(path: Path) -> ReviewabilityConfig:
    """Parse a TOML config file and return a ReviewabilityConfig.

    Configuration is read from a ``[reviewability]`` section if present,
    otherwise from the top-level table. Unknown keys are silently ignored.
    """
    with open(path, "rb") as f:
        data = tomllib.load(f)

    section = data.get("reviewability", data)
    known = {k: v for k, v in section.items() if k in _KNOWN_FIELDS}
    return ReviewabilityConfig(**known)
