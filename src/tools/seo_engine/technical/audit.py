"""Technical SEO audit persistence (LEDGER — S2). Non-authoritative."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.tools.runtime_paths import REPO_ROOT
from src.tools.seo_engine.technical.models import TechnicalPageReport, TechnicalSiteReport

TECH_OUTPUT_DIR = REPO_ROOT / "output" / "seo" / "technical"


def write_technical_audit(
    result: TechnicalSiteReport | TechnicalPageReport,
    *,
    output_dir: Path | None = None,
) -> Path:
    root = Path(output_dir) if output_dir is not None else TECH_OUTPUT_DIR
    root.mkdir(parents=True, exist_ok=True)
    if isinstance(result, TechnicalSiteReport):
        path = root / "site.json"
    else:
        path = root / f"{result.slug or 'unknown'}.json"
    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authoritative": False,
        "engine": "technical_seo_phase1",
        "s1_readiness_contract": "UNCHANGED",
        "mutates_content": False,
        "report": result.to_dict(),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
