"""
Tests for CampusIQ student risk assessment.
"""

import pytest

from analytics.risk import (
    calculate_risk_score,
    classify_risk,
    assess_student_risk,
    get_risk_factors,
)


def test_calculate_risk_score():
    """Test the weighted risk calculation."""

    student = {
        "attendance": 59,
        "assignment_score": 40,
        "exam_score": 35,
        "engagement_score": 30,
    }

    score = calculate_risk_score(student)

    assert score == 58.75


def test_perfect_student_has_zero_risk():
    """Perfect academic indicators should produce zero risk."""

    student = {
        "attendance": 100,
        "assignment_score": 100,
        "exam_score": 100,
        "engagement_score": 100,
    }

    assert calculate_risk_score(student) == 0.0


def test_zero_scores_produce_maximum_risk():
    """Zero academic indicators should produce maximum risk."""

    student = {
        "attendance": 0,
        "assignment_score": 0,
        "exam_score": 0,
        "engagement_score": 0,
    }

    assert calculate_risk_score(student) == 100.0


@pytest.mark.parametrize(
    "score, expected_level",
    [
        (0, "Low"),
        (29.99, "Low"),
        (30, "Medium"),
        (59.99, "Medium"),
        (60, "High"),
        (100, "High"),
    ],
)
def test_classify_risk(score, expected_level):
    """Test risk classification boundaries."""

    assert classify_risk(score) == expected_level


def test_assess_student_risk():
    """Test the complete risk assessment response."""

    student = {
        "attendance": 59,
        "assignment_score": 40,
        "exam_score": 35,
        "engagement_score": 30,
    }

    result = assess_student_risk(student)

    assert result["risk_score"] == 58.75
    assert result["risk_level"] == "Medium"


def test_get_risk_factors():
    """Verify that low academic indicators are identified."""

    student = {
        "attendance": 60,
        "assignment_score": 40,
        "exam_score": 35,
        "engagement_score": 25,
    }

    factors = get_risk_factors(student)

    assert "Low attendance" in factors
    assert "Low assignment performance" in factors
    assert "Low examination performance" in factors
    assert "Low student engagement" in factors


def test_no_risk_factors_for_strong_student():
    """Strong indicators should produce no risk factors."""

    student = {
        "attendance": 95,
        "assignment_score": 90,
        "exam_score": 92,
        "engagement_score": 85,
    }

    assert get_risk_factors(student) == []


def test_missing_values():
    """Missing metrics should default to zero."""

    assert calculate_risk_score({}) == 100.0


def test_invalid_values():
    """Invalid values should safely default to zero."""

    student = {
        "attendance": "invalid",
        "assignment_score": None,
        "exam_score": 50,
        "engagement_score": 50,
    }

    assert calculate_risk_score(student) == 75.0