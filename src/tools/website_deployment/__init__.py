"""Website Deployment Adapter (Sprint M5).

Packages the public subset of Static Provider output and prepares host transport.
Lives outside Website Engine Core / Static Provider v1.0 frozen contracts.

Does NOT own: Markdown render, Publishing orchestration, or hosting platforms.
"""

from src.tools.website_deployment.adapter import DeploymentAdapter, DeploymentResult
from src.tools.website_deployment.contract import (
    DEFAULT_DEPLOY_ROOT,
    DEFAULT_SOURCE_ROOT,
    OPERATOR_ARTIFACT_NAMES,
    PUBLIC_ROOT_FEED_NAMES,
    PUBLIC_PAGE_ARTIFACT_NAME,
)
from src.tools.website_deployment.export import export_public_package
from src.tools.website_deployment.manifest import DeploymentManifest, write_manifest

__all__ = [
    "DEFAULT_DEPLOY_ROOT",
    "DEFAULT_SOURCE_ROOT",
    "DeploymentAdapter",
    "DeploymentManifest",
    "DeploymentResult",
    "OPERATOR_ARTIFACT_NAMES",
    "PUBLIC_PAGE_ARTIFACT_NAME",
    "PUBLIC_ROOT_FEED_NAMES",
    "export_public_package",
    "write_manifest",
]
