"""Website provider registry (Sprint M3).

Resolves named providers for Website Engine publish paths.
No WordPress/Ghost/network adapters registered here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from src.tools.website_engine.provider import StubWebsiteProvider, WebsiteProvider
from src.tools.website_engine.static_provider import StaticWebsiteProvider

ProviderFactory = Callable[[Path | None], WebsiteProvider]

_REGISTRY: dict[str, ProviderFactory] = {}


def register_provider(name: str, factory: ProviderFactory) -> None:
    """Register or replace a provider factory under ``name``."""
    key = (name or "").strip().lower()
    if not key:
        raise ValueError("Provider name must be non-empty")
    _REGISTRY[key] = factory


def list_providers() -> list[str]:
    """Return sorted registered provider names."""
    return sorted(_REGISTRY.keys())


def get_provider(
    name: str,
    *,
    output_dir: Path | str | None = None,
) -> WebsiteProvider:
    """Instantiate a registered provider by name.

    Raises ``KeyError`` when ``name`` is unknown.
    """
    key = (name or "").strip().lower()
    if key not in _REGISTRY:
        known = ", ".join(list_providers()) or "(none)"
        raise KeyError(f"Unknown website provider {name!r}; known: {known}")
    out: Path | None
    if output_dir is None:
        out = None
    else:
        out = Path(output_dir)
    return _REGISTRY[key](out)


def _ensure_defaults() -> None:
    if "static" not in _REGISTRY:
        register_provider(
            "static",
            lambda output_dir: StaticWebsiteProvider(output_dir=output_dir),
        )
    if "stub" not in _REGISTRY:
        register_provider(
            "stub",
            lambda output_dir: StubWebsiteProvider(output_dir=output_dir),
        )


_ensure_defaults()
