"""
Metrics Collector - Utility for Collecting and Aggregating Metrics

This module provides utilities for collecting, storing, and aggregating
performance metrics from various components of the infrastructure.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict
from enum import Enum

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class MetricType(str, Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricPoint:
    """A single metric data point."""

    def __init__(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        labels: Dict[str, str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.name = name
        self.value = value
        self.metric_type = metric_type
        self.labels = labels or {}
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat()
        }


class MetricsCollector:
    """
    Collector for infrastructure metrics.

    Provides functionality to collect, store, aggregate, and export metrics
    from various infrastructure components.
    """

    def __init__(self):
        self._metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._running = False
        self._cleanup_task = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the metrics collector."""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Metrics collector started")

    async def stop(self) -> None:
        """Stop the metrics collector."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collector stopped")

    async def _cleanup_loop(self) -> None:
        """Periodically cleanup old metrics."""
        while self._running:
            try:
                await self._cleanup_old_metrics()
                await asyncio.sleep(settings.METRICS_AGGREGATION_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in metrics cleanup loop", error=str(e))
                await asyncio.sleep(60)

    async def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than retention period."""
        async with self._lock:
            cutoff = datetime.utcnow() - timedelta(seconds=settings.METRICS_RETENTION_PERIOD)

            for name in list(self._metrics.keys()):
                self._metrics[name] = [
                    m for m in self._metrics[name]
                    if m.timestamp > cutoff
                ]

                # Remove empty metric lists
                if not self._metrics[name]:
                    del self._metrics[name]

    async def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Dict[str, str] = None
    ) -> None:
        """
        Increment a counter metric.

        Counters only go up and are typically used for counting events.
        """
        async with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value

            point = MetricPoint(
                name=name,
                value=self._counters[key],
                metric_type=MetricType.COUNTER,
                labels=labels
            )
            self._metrics[name].append(point)

    async def set_gauge(
        self,
        name: str,
        value: float,
        labels: Dict[str, str] = None
    ) -> None:
        """
        Set a gauge metric.

        Gauges can go up or down and represent a current value.
        """
        async with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value

            point = MetricPoint(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                labels=labels
            )
            self._metrics[name].append(point)

    async def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Dict[str, str] = None
    ) -> None:
        """
        Observe a value for a histogram metric.

        Histograms sample observations and count them in configurable buckets.
        """
        async with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)

            point = MetricPoint(
                name=name,
                value=value,
                metric_type=MetricType.HISTOGRAM,
                labels=labels
            )
            self._metrics[name].append(point)

    async def record_timing(
        self,
        name: str,
        duration_seconds: float,
        labels: Dict[str, str] = None
    ) -> None:
        """
        Record a timing measurement.

        This is a convenience method for recording durations.
        """
        await self.observe_histogram(name, duration_seconds, labels)

    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create a unique key for a metric with labels."""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    async def get_metric(
        self,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get metric data points for a specific metric."""
        async with self._lock:
            points = self._metrics.get(name, [])

            if start_time:
                points = [p for p in points if p.timestamp >= start_time]
            if end_time:
                points = [p for p in points if p.timestamp <= end_time]

            return [p.to_dict() for p in points]

    async def get_counter_value(
        self,
        name: str,
        labels: Dict[str, str] = None
    ) -> float:
        """Get current counter value."""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)

    async def get_gauge_value(
        self,
        name: str,
        labels: Dict[str, str] = None
    ) -> Optional[float]:
        """Get current gauge value."""
        key = self._make_key(name, labels)
        return self._gauges.get(key)

    async def get_histogram_stats(
        self,
        name: str,
        labels: Dict[str, str] = None
    ) -> Dict[str, float]:
        """Get histogram statistics (min, max, avg, count, percentiles)."""
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])

        if not values:
            return {}

        sorted_values = sorted(values)
        count = len(values)

        return {
            "count": count,
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / count,
            "sum": sum(values),
            "p50": self._percentile(sorted_values, 50),
            "p90": self._percentile(sorted_values, 90),
            "p95": self._percentile(sorted_values, 95),
            "p99": self._percentile(sorted_values, 99)
        }

    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0

        index = int(len(sorted_values) * percentile / 100)
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]

    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        async with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    k: await self.get_histogram_stats(k.split("{")[0])
                    for k in self._histograms.keys()
                }
            }

    async def aggregate_metrics(
        self,
        name: str,
        interval_seconds: int = 60,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Aggregate metrics over time intervals.

        Returns average values for each time interval.
        """
        points = await self.get_metric(name, start_time, end_time)

        if not points:
            return []

        # Group by interval
        interval_delta = timedelta(seconds=interval_seconds)
        aggregated = defaultdict(list)

        for point in points:
            timestamp = datetime.fromisoformat(point["timestamp"])
            # Round down to interval
            interval_start = timestamp - timedelta(
                seconds=timestamp.timestamp() % interval_seconds
            )
            aggregated[interval_start].append(point["value"])

        # Calculate averages
        result = []
        for interval_start, values in sorted(aggregated.items()):
            result.append({
                "timestamp": interval_start.isoformat(),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "count": len(values)
            })

        return result

    async def export_prometheus_format(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns a string that can be scraped by Prometheus.
        """
        lines = []

        # Export counters
        for key, value in self._counters.items():
            name = key.split("{")[0] if "{" in key else key
            labels = key[key.find("{"):] if "{" in key else ""
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name}{labels} {value}")

        # Export gauges
        for key, value in self._gauges.items():
            name = key.split("{")[0] if "{" in key else key
            labels = key[key.find("{"):] if "{" in key else ""
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name}{labels} {value}")

        # Export histogram summaries
        for key, values in self._histograms.items():
            if not values:
                continue

            name = key.split("{")[0] if "{" in key else key
            labels = key[key.find("{"):] if "{" in key else ""
            stats = await self.get_histogram_stats(name)

            lines.append(f"# TYPE {name} summary")
            lines.append(f'{name}_count{labels} {stats["count"]}')
            lines.append(f'{name}_sum{labels} {stats["sum"]}')

        return "\n".join(lines)

    async def reset(self) -> None:
        """Reset all metrics."""
        async with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            logger.info("Metrics collector reset")


class Timer:
    """Context manager for timing code blocks."""

    def __init__(
        self,
        collector: MetricsCollector,
        metric_name: str,
        labels: Dict[str, str] = None
    ):
        self.collector = collector
        self.metric_name = metric_name
        self.labels = labels
        self.start_time = None

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        await self.collector.record_timing(
            self.metric_name,
            duration,
            self.labels
        )
