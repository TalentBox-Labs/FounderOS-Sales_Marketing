"""SEO readiness audit persistence (LEDGER — S1).

Additive, non-authoritative filesystem read-model under output/seo/.
Never writes to input/ content bundles or Website Engine source.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.tools.runtime_paths import REPO_ROOT
from src.tools.seo_engine.models import PageReadinessResult, SiteReadinessResult

SEO_OUTPUT_DIR = REPO_ROOT / "output" / "seo" / "readiness"


def seo_audit_dir() -> Path:
    return SEO_OUTPUT_DIR


def write_page_audit(result: PageReadinessResult, *, output_dir: Path | None = None) -> Path:
    """Persist a single page readiness report (inspectable JSON)."""
    root = Path(output_dir) if output_dir is not None else SEO_OUTPUT_DIR
    root.mkdir(parents=True, exist_ok=True)
    slug = result.slug or "unknown"
    path = root / f"{slug}.json"
    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authoritative": False,
        "source_of_truth": "Website Engine artifacts + SEO Engine analysis",
        "mutates_content": False,
        "report": result.to_dict(),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def write_site_audit(result: SiteReadinessResult, *, output_dir: Path | None = None) -> Path:
    """Persist site-level readiness aggregate."""
    root = Path(output_dir) if output_dir is not None else SEO_OUTPUT_DIR
    root.mkdir(parents=True, exist_ok=True)
    path = root / "site.json"
    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authoritative": False,
        "source_of_truth": "Website Engine artifacts + SEO Engine analysis",
        "mutates_content": False,
        "report": result.to_dict(),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
