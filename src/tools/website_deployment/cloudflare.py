"""Cloudflare Pages configuration generation (no network calls)."""

from __future__ import annotations

from pathlib import Path

from src.tools.website_deployment.contract import CLOUDFLARE_CONFIG_DIRNAME

DEFAULT_PAGES_PROJECT = "founder-website"
WRANGLER_FILENAME = "wrangler.toml"
HEADERS_FILENAME = "_headers"
REDIRECTS_FILENAME = "_redirects"
README_FILENAME = "README-CLOUDFLARE-PAGES.md"


def wrangler_toml_content(*, project_name: str = DEFAULT_PAGES_PROJECT) -> str:
    """Minimal Pages project metadata for operator-driven Direct Upload."""
    return (
        f'name = "{project_name}"\n'
        'compatibility_date = "2024-09-23"\n'
        "\n"
        "# FounderOS ships a pre-built static tree (no Pages build command).\n"
        "# From the exported package directory:\n"
        f"#   npx wrangler pages deploy . --project-name={project_name}\n"
    )


def default_headers_content() -> str:
    return (
        "# Deny operator artifacts if ever copied by mistake (public export excludes them).\n"
        "/*/metadata.json\n"
        "  X-Robots-Tag: noindex\n"
        "  Cache-Control: no-store\n"
        "\n"
        "/*/source.md\n"
        "  X-Robots-Tag: noindex\n"
        "  Cache-Control: no-store\n"
    )


def cloudflare_readme_content(*, project_name: str = DEFAULT_PAGES_PROJECT) -> str:
    return (
        "# Cloudflare Pages — FounderOS static package\n"
        "\n"
        "This directory holds generated configuration for **Direct Upload** of the\n"
        "public subset produced by the Deployment Adapter.\n"
        "\n"
        "## Prerequisites\n"
        "\n"
        "- Cloudflare account and Pages project (create in dashboard; not automated here)\n"
        "- API token or `wrangler login` (store in Shared Platform secrets — never in repo)\n"
        "- Custom domain DNS aligned with Website Engine `canonical_url`\n"
        "\n"
        "## Deploy (operator)\n"
        "\n"
        "From the **package root** (parent of this `cloudflare/` folder), after export:\n"
        "\n"
        "```bash\n"
        f"npx wrangler pages deploy . --project-name={project_name}\n"
        "```\n"
        "\n"
        "## Rollback\n"
        "\n"
        "Use Cloudflare Pages dashboard **Deployments → Rollback to this deployment**,\n"
        "or local rollback metadata under `output/website-deploy/rollback-history.jsonl`.\n"
        "\n"
        "FounderOS Core and Static Provider do not call Cloudflare APIs.\n"
    )


def write_cloudflare_config(
    deploy_root: Path,
    *,
    project_name: str = DEFAULT_PAGES_PROJECT,
) -> dict[str, Path]:
    """Write wrangler + helper files under deploy_root/cloudflare/."""
    cfg_dir = deploy_root / CLOUDFLARE_CONFIG_DIRNAME
    cfg_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "wrangler": cfg_dir / WRANGLER_FILENAME,
        "headers_template": cfg_dir / HEADERS_FILENAME,
        "redirects_template": cfg_dir / REDIRECTS_FILENAME,
        "readme": cfg_dir / README_FILENAME,
    }
    paths["wrangler"].write_text(wrangler_toml_content(project_name=project_name), encoding="utf-8")
    paths["headers_template"].write_text(default_headers_content(), encoding="utf-8")
    paths["redirects_template"].write_text("# Static site — no redirects by default\n", encoding="utf-8")
    paths["readme"].write_text(cloudflare_readme_content(project_name=project_name), encoding="utf-8")
    return paths
