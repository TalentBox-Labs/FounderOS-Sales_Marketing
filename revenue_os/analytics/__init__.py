"""Business intelligence and analytics system."""

from revenue_os.analytics.core import (
    AnalyticsEngine,
    DimensionalAnalytics,
    TrendAnalysis,
    MetricType,
    DashboardType,
)
from revenue_os.analytics.dashboards import (
    DashboardBuilder,
    ExecutiveDashboard,
    SalesDashboard,
    CSMDashboard,
    MarketingDashboard,
    OperationsDashboard,
)

__all__ = [
    "AnalyticsEngine",
    "DimensionalAnalytics",
    "TrendAnalysis",
    "MetricType",
    "DashboardType",
    "DashboardBuilder",
    "ExecutiveDashboard",
    "SalesDashboard",
    "CSMDashboard",
    "MarketingDashboard",
    "OperationsDashboard",
]
