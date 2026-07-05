"""Load pack reference JSON assets."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


def assets_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(*parts: str) -> Any:
    path = assets_dir() / Path(*parts)
    if not path.exists():
        return {} if parts[-1].endswith(".json") else []
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def etf_catalog() -> dict[str, dict[str, str]]:
    return _load_json("reference", "etf_catalog.json")


@lru_cache(maxsize=1)
def equity_gics_seed() -> dict[str, dict[str, str]]:
    return _load_json("reference", "equity_gics_seed.json")


@lru_cache(maxsize=1)
def theme_registry_seed() -> list[dict[str, str]]:
    return _load_json("theme-rules", "theme_registry_seed.json")


@lru_cache(maxsize=1)
def sector_to_theme() -> dict[str, str]:
    return _load_json("theme-rules", "sector_to_theme.json")


@lru_cache(maxsize=1)
def symbol_theme_overrides() -> dict[str, dict[str, str]]:
    return _load_json("theme-rules", "symbol_overrides.json")


CASH_LIKE = frozenset({"SGOV", "BIL", "SHV", "VMFXX", "SPAXX", "FDRXX", "SPRXX", "VMMXX"})

SUBCLASS_TO_THEME = {
    "Treasury ETF": "THEME_DEFENSIVE_FIXED_INCOME",
    "TIPS ETF": "THEME_DEFENSIVE_FIXED_INCOME",
    "Physical Precious Metal Trust": "THEME_PRECIOUS_METALS",
    "Precious Metal Miners ETF": "THEME_PRECIOUS_METALS",
    "Broad Market ETF": "THEME_FACTOR_BETA",
    "Factor ETF": "THEME_FACTOR_BETA",
    "Small Cap ETF": "THEME_FACTOR_BETA",
    "International Equity ETF": "THEME_INTERNATIONAL",
    "Emerging Markets ETF": "THEME_INTERNATIONAL",
    "SPAC ETF": "THEME_TACTICAL",
    "Crypto ETF": "THEME_TACTICAL",
    "Thematic ETF": "THEME_TECH_AI",
    "MLP ETF": "THEME_ENERGY_COMMODITY",
    "Energy ETF": "THEME_ENERGY_COMMODITY",
    "Uranium ETF": "THEME_ENERGY_COMMODITY",
    "Rare Earth ETF": "THEME_ENERGY_COMMODITY",
    "Covered Call ETF": "THEME_FACTOR_BETA",
}
