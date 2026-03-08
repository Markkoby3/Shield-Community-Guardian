import pytest
from backend.models import Report
from backend.services.filter import filter_reports, classify_alert
from backend.services.pipeline import process_reports


# ── filter_reports ─────────────────────────────────────────────────────────────

def test_filter_keeps_signal():
    reports = [
        Report(text="phishing email alert", location="national"),
        Report(text="my wifi sucks again", location="Austin"),
    ]
    result = filter_reports(reports)
    assert len(result) == 1
    assert result[0].text == "phishing email alert"


def test_filter_signal_beats_noise():
    reports = [Report(text="wifi sucks but phishing detected", location="Austin")]
    result = filter_reports(reports)
    assert len(result) == 1


def test_filter_empty():
    assert filter_reports([]) == []


def test_filter_no_signal():
    reports = [Report(text="sunny day in the park", location="Austin")]
    assert filter_reports(reports) == []


# ── classify_alert ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected_category,expected_severity", [
    ("major phishing campaign detected",  "cyber_threat",    "high"),
    ("data breach reported at company",   "cyber_threat",    "high"),
    ("new scam targeting seniors",        "scam_alert",      "medium"),
    ("car theft on main street",          "local_crime",     "medium"),
    ("power outage across downtown",      "infrastructure",  "medium"),
    ("community meeting tonight",         "general",         "low"),
])
def test_classify_alert(text, expected_category, expected_severity):
    category, severity = classify_alert(text)
    assert category == expected_category
    assert severity == expected_severity


# ── process_reports ────────────────────────────────────────────────────────────

def test_process_filters_by_location():
    reports = [
        Report(text="scam alert in Austin", location="Austin"),
        Report(text="scam alert in Dallas", location="Dallas"),
        Report(text="national breach warning", location="national"),
    ]
    response = process_reports(reports, user_location="Austin")
    locations = {a.location for a in response.alerts}
    assert "Dallas" not in locations
    assert response.processed == 2
    assert response.filtered_out == 1


def test_process_returns_typed_results():
    reports = [Report(text="phishing email alert", location="national")]
    response = process_reports(reports, user_location="Austin")
    assert len(response.alerts) == 1
    alert = response.alerts[0]
    assert alert.severity in ("high", "medium", "low")
    assert alert.method in ("AI", "fallback")
