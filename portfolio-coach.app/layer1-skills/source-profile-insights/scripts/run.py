#!/usr/bin/env python3
"""PortfolioCoach skill: source-profile-insights. See SKILL.md."""
from __future__ import annotations

import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PACK_ROOT / "assets" / "pc-lib"))

from pc_lib.cli import run_main  # noqa: E402
from pc_lib.skills.source_profile_insights import run  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run_main("source-profile-insights", run))
