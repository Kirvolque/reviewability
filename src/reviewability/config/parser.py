import tomllib
from dataclasses import fields
from pathlib import Path

from reviewability.config.models import ReviewabilityConfig

_KNOWN_FIELDS: frozenset[str] = frozenset(f.name for f in fields(ReviewabilityConfig))

_BUNDLED_CONFIG: Path = Path(__file__).parent / "reviewability.toml"


def parse_config(path: Path | None = None) -> ReviewabilityConfig:
    """Parse a TOML config file and return a ReviewabilityConfig.

    If a path is provided and the file exists, it is loaded as-is — it must
    contain all mandatory fields. If the path does not exist or is None,
    the bundled default config is used.

    Raises ``TypeError`` if any mandatory field is missing.
    """
    config_path = path if path is not None and path.exists() else _BUNDLED_CONFIG

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    values = {key: value for key, value in raw.items() if key in _KNOWN_FIELDS}
    return ReviewabilityConfig(**values)
