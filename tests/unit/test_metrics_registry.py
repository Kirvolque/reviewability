from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import FileDiff, Hunk
from reviewability.domain.report import Analysis
from reviewability.metrics.base import FileMetric, HunkMetric, OverallMetric
from reviewability.metrics.registry import MetricRegistry


class _SimpleHunkMetric(HunkMetric):
    name = "test.hunk_metric"
    value_type = MetricValueType.INTEGER
    description = "A test hunk metric"
    remediation = "fix it"

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(self.name, 0, self.value_type)


class _AnotherHunkMetric(HunkMetric):
    name = "test.hunk_metric_2"
    value_type = MetricValueType.INTEGER
    description = "Another hunk metric"
    remediation = ""

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(self.name, 0, self.value_type)


class _SimpleFileMetric(FileMetric):
    name = "test.file_metric"
    value_type = MetricValueType.INTEGER
    description = "A test file metric"
    remediation = ""

    def calculate(self, file: FileDiff) -> MetricValue:
        return MetricValue(self.name, 0, self.value_type)


class _AnotherFileMetric(FileMetric):
    name = "test.file_metric_2"
    value_type = MetricValueType.INTEGER
    description = "Another file metric"
    remediation = ""

    def calculate(self, file: FileDiff) -> MetricValue:
        return MetricValue(self.name, 0, self.value_type)


class _SimpleOverallMetric(OverallMetric):
    name = "test.overall_metric"
    value_type = MetricValueType.INTEGER
    description = "A test overall metric"
    remediation = ""

    def calculate(self, hunks: list[Analysis], files: list[Analysis]) -> MetricValue:
        return MetricValue(self.name, 0, self.value_type)


class _AnotherOverallMetric(OverallMetric):
    name = "test.overall_metric_2"
    value_type = MetricValueType.INTEGER
    description = "Another overall metric"
    remediation = ""

    def calculate(self, hunks: list[Analysis], files: list[Analysis]) -> MetricValue:
        return MetricValue(self.name, 0, self.value_type)


# --- MetricRegistry tests ---


def test_empty_registry():
    registry = MetricRegistry()
    assert registry.hunk_metrics() == []
    assert registry.file_metrics() == []
    assert registry.overall_metrics() == []


def test_add_hunk_metric():
    registry = MetricRegistry()
    metric = _SimpleHunkMetric()
    registry.add(metric)
    assert registry.hunk_metrics() == [metric]
    assert registry.file_metrics() == []
    assert registry.overall_metrics() == []


def test_add_multiple_hunk_metrics():
    registry = MetricRegistry()
    m1 = _SimpleHunkMetric()
    m2 = _AnotherHunkMetric()
    registry.add(m1)
    registry.add(m2)
    assert len(registry.hunk_metrics()) == 2
    assert m1 in registry.hunk_metrics()
    assert m2 in registry.hunk_metrics()


def test_add_mixed_metrics():
    registry = MetricRegistry()
    hm = _SimpleHunkMetric()
    fm = _SimpleFileMetric()
    om = _SimpleOverallMetric()
    registry.add(hm)
    registry.add(fm)
    registry.add(om)
    assert registry.hunk_metrics() == [hm]
    assert registry.file_metrics() == [fm]
    assert registry.overall_metrics() == [om]


def test_duplicate_hunk_metric_is_replaced():
    registry = MetricRegistry()

    class _Replacement(HunkMetric):
        name = "test.hunk_metric"
        value_type = MetricValueType.INTEGER
        description = "Replacement"
        remediation = ""

        def calculate(self, hunk: Hunk) -> MetricValue:
            return MetricValue(self.name, 99, self.value_type)

    original = _SimpleHunkMetric()
    replacement = _Replacement()
    registry.add(original)
    registry.add(replacement)
    metrics = registry.hunk_metrics()
    assert len(metrics) == 1
    assert metrics[0] is replacement


def test_hunk_metrics_returns_new_list():
    # Mutating the returned list should not affect the registry
    registry = MetricRegistry()
    registry.add(_SimpleHunkMetric())
    lst1 = registry.hunk_metrics()
    lst1.clear()
    assert len(registry.hunk_metrics()) == 1
