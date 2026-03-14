import tomllib
from dataclasses import fields
from pathlib import Path

from reviewability.config.models import ReviewabilityConfig

_KNOWN_FIELDS: frozenset[str] = frozenset(f.name for f in fields(ReviewabilityConfig))

_SECTION_PREFIX_MAP: dict[str, str] = {
    "movement_detection": "movement_",
}


def parse_config(path: Path) -> ReviewabilityConfig:
    """Parse a TOML config file and return a ReviewabilityConfig.

    Top-level keys map directly to config fields. Subsection keys are prefixed
    with the section's mapped prefix before lookup (e.g. ``[movement_detection]``
    key ``hunk_min_lines`` maps to field ``movement_hunk_min_lines``).
    Unknown keys are silently ignored.
    """
    with open(path, "rb") as f:
        data = tomllib.load(f)

    known: dict[str, object] = {}

    for key, value in data.items():
        if isinstance(value, dict):
            prefix = _SECTION_PREFIX_MAP.get(key, f"{key}_")
            for subkey, subvalue in value.items():
                field_name = f"{prefix}{subkey}"
                if field_name in _KNOWN_FIELDS:
                    known[field_name] = subvalue
        elif key in _KNOWN_FIELDS:
            known[key] = value

    return ReviewabilityConfig(**known)
