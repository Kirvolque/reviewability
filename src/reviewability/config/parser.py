import tomllib
from dataclasses import fields
from pathlib import Path

from reviewability.config.models import ReviewabilityConfig

_KNOWN_FIELDS: frozenset[str] = frozenset(f.name for f in fields(ReviewabilityConfig))

_BUNDLED_CONFIG: Path = Path(__file__).parent / "reviewability.toml"

_SECTION_PREFIX_MAP: dict[str, str] = {
    "movement_detection": "movement_",
    "rewrite_scoring": "rewrite_",
}


def _flatten_toml(data: dict) -> dict[str, object]:
    """Convert a TOML dict (with possible subsections) to flat config field names."""
    flat: dict[str, object] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            prefix = _SECTION_PREFIX_MAP.get(key, f"{key}_")
            for subkey, subvalue in value.items():
                field_name = f"{prefix}{subkey}"
                if field_name in _KNOWN_FIELDS:
                    flat[field_name] = subvalue
        elif key in _KNOWN_FIELDS:
            flat[key] = value
    return flat


def parse_config(path: Path | None = None) -> ReviewabilityConfig:
    """Parse a TOML config file and return a ReviewabilityConfig.

    If a path is provided and the file exists, it is loaded as-is — it must
    contain all mandatory fields. If the path does not exist or is None,
    the bundled default config is used.

    Raises ``TypeError`` if any mandatory field is missing.
    """
    config_path = path if path is not None and path.exists() else _BUNDLED_CONFIG

    with open(config_path, "rb") as f:
        values = _flatten_toml(tomllib.load(f))

    return ReviewabilityConfig(**values)
