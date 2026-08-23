"""Marketing automation system."""

from revenue_os.marketing.email_automation import (
    EmailSequenceManager,
    LeadScoringEngine,
    BehaviorTriggerEngine,
)
from revenue_os.marketing.lead_nurturing import (
    NurtureCampaignManager,
    SegmentationEngine,
    ReengagementCampaignManager,
)

__all__ = [
    "EmailSequenceManager",
    "LeadScoringEngine",
    "BehaviorTriggerEngine",
    "NurtureCampaignManager",
    "SegmentationEngine",
    "ReengagementCampaignManager",
]
