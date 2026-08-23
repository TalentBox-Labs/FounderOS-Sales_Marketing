"""DEMO-D1.1 — demo metric sample values tolerate null targets."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from revenue_os.analytics.core import AnalyticsEngine, AnalyticsMetric, MetricType

_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "init_demo_db",
    _ROOT / "scripts" / "init_demo_db.py",
)
assert _SPEC is not None and _SPEC.loader is not None
init_demo_db = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(init_demo_db)


def _metric(
    metric_type: MetricType,
    *,
    target_value: float | None,
    name: str = "Demo",
) -> AnalyticsMetric:
    return AnalyticsMetric(
        id=f"metric_{metric_type.value}_{target_value}",
        name=name,
        metric_type=metric_type,
        calculation="demo",
        unit="u",
        description="demo",
        target_value=target_value,
    )


def test_present_target_value_is_preserved() -> None:
    metric = _metric(MetricType.PERCENTAGE, target_value=30.0)
    assert init_demo_db.demo_metric_base_target(metric) == 30.0
    value = init_demo_db.demo_metric_sample_value(metric, 3)
    assert 20.0 <= value <= 40.0


def test_none_target_value_does_not_crash() -> None:
    for metric_type in MetricType:
        metric = _metric(metric_type, target_value=None)
        value = init_demo_db.demo_metric_sample_value(metric, 1)
        assert isinstance(value, float)
        assert value >= 0.0


def test_generated_type_values_remain_valid() -> None:
    revenue = init_demo_db.demo_metric_sample_value(
        _metric(MetricType.REVENUE, target_value=None), 2
    )
    percentage = init_demo_db.demo_metric_sample_value(
        _metric(MetricType.PERCENTAGE, target_value=None), 2
    )
    time_value = init_demo_db.demo_metric_sample_value(
        _metric(MetricType.TIME, target_value=None), 2
    )
    count = init_demo_db.demo_metric_sample_value(
        _metric(MetricType.COUNT, target_value=None), 2
    )
    assert revenue > 0
    assert 0.0 <= percentage <= 100.0
    assert time_value >= 0.0
    assert count >= 0.0


def test_repeated_demo_generation_does_not_throw() -> None:
    AnalyticsEngine._metrics = {}
    AnalyticsEngine._data_points = []
    AnalyticsEngine._hydrated = True
    AnalyticsEngine.register_metric(_metric(MetricType.PERCENTAGE, target_value=30.0))
    AnalyticsEngine.register_metric(_metric(MetricType.COUNT, target_value=None, name="Null count"))
    init_demo_db.record_demo_data_points()
    first = len(AnalyticsEngine._data_points)
    init_demo_db.record_demo_data_points()
    assert len(AnalyticsEngine._data_points) == first * 2
    AnalyticsEngine._metrics = {}
    AnalyticsEngine._data_points = []
    AnalyticsEngine._hydrated = False
