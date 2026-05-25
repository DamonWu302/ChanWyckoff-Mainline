from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.structure.recognition import Bar30m, StructureRecognitionService


def make_bar(index: int, high: str, low: str, close: str) -> Bar30m:
    return Bar30m(
        bar_time=datetime(2026, 5, 25, 9, 30, tzinfo=timezone.utc) + timedelta(minutes=30 * index),
        open=Decimal(close),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=100000 + index * 1000,
        amount=Decimal("100000000"),
    )


def test_recognizes_typical_30m_platform_boundaries() -> None:
    bars = [
        make_bar(0, "10.30", "9.80", "10.00"),
        make_bar(1, "10.50", "9.90", "10.20"),
        make_bar(2, "10.40", "9.85", "10.05"),
        make_bar(3, "10.55", "9.95", "10.30"),
        make_bar(4, "10.45", "9.90", "10.10"),
        make_bar(5, "10.60", "10.00", "10.35"),
        make_bar(6, "10.50", "9.92", "10.15"),
        make_bar(7, "10.58", "10.02", "10.40"),
        make_bar(8, "10.52", "9.98", "10.25"),
        make_bar(9, "10.62", "10.05", "10.45"),
    ]
    service = StructureRecognitionService()

    result = service.analyze(bars)

    assert len(result.structures) == 1
    structure = result.structures[0]
    assert structure.label == "statistical_platform"
    assert structure.upper == Decimal("10.62")
    assert structure.lower == Decimal("9.80")
    assert structure.mid == Decimal("10.21")
    assert structure.duration_bars == 10
    assert structure.upper_tests >= 3
    assert structure.quality_score >= 70


def test_does_not_overreport_one_way_downtrend_as_platform() -> None:
    bars = [
        make_bar(0, "20.0", "19.2", "19.5"),
        make_bar(1, "19.5", "18.8", "19.0"),
        make_bar(2, "19.0", "18.1", "18.4"),
        make_bar(3, "18.4", "17.7", "18.0"),
        make_bar(4, "18.0", "17.0", "17.2"),
        make_bar(5, "17.2", "16.2", "16.5"),
        make_bar(6, "16.6", "15.7", "16.0"),
        make_bar(7, "16.0", "15.0", "15.2"),
        make_bar(8, "15.3", "14.5", "14.8"),
        make_bar(9, "14.9", "14.0", "14.2"),
    ]
    service = StructureRecognitionService()

    result = service.analyze(bars)

    assert result.structures == []


def test_recognizes_converging_platform_and_outputs_fractals_and_strokes() -> None:
    bars = [
        make_bar(0, "11.00", "9.00", "10.00"),
        make_bar(1, "10.90", "9.10", "10.20"),
        make_bar(2, "10.80", "9.20", "9.90"),
        make_bar(3, "10.70", "9.30", "10.30"),
        make_bar(4, "10.60", "9.40", "10.10"),
        make_bar(5, "10.50", "9.50", "10.35"),
        make_bar(6, "10.45", "9.55", "10.00"),
        make_bar(7, "10.40", "9.60", "10.25"),
        make_bar(8, "10.35", "9.65", "10.15"),
        make_bar(9, "10.30", "9.70", "10.20"),
    ]
    service = StructureRecognitionService()

    result = service.analyze(bars)

    assert len(result.structures) == 1
    assert result.structures[0].label == "converging_platform"
    assert result.structures[0].quality_score >= 70
    assert len(result.fractals) >= 2
    assert len(result.strokes) >= 1


def test_rejects_fake_platform_with_low_overlap_and_wide_amplitude() -> None:
    bars = [
        make_bar(0, "10.2", "9.8", "10.0"),
        make_bar(1, "12.5", "11.8", "12.2"),
        make_bar(2, "9.2", "8.5", "8.8"),
        make_bar(3, "13.4", "12.6", "13.0"),
        make_bar(4, "8.6", "7.9", "8.1"),
        make_bar(5, "14.0", "13.2", "13.7"),
        make_bar(6, "9.0", "8.2", "8.4"),
        make_bar(7, "13.8", "13.0", "13.3"),
        make_bar(8, "8.8", "8.0", "8.2"),
        make_bar(9, "14.2", "13.4", "13.9"),
    ]
    service = StructureRecognitionService()

    result = service.analyze(bars)

    assert result.structures == []
