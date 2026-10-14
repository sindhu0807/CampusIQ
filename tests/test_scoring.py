"""
Tests for CampusIQ student performance scoring.
"""

import pytest

from analytics.scoring import (
    calculate_performance_score,
    calculate_student_metrics,
)


def test_calculate_performance_score():
    """Test the weighted performance score."""

    student = {
        "attendance": 90,
        "assignment_score": 80,
        "exam_score": 75,
        "engagement_score": 85,
    }

    score = calculate_performance_score(student)

    assert score == 80.75


def test_perfect_performance_score():
    """A student with perfect scores should receive 100."""

    student = {
        "attendance": 100,
        "assignment_score": 100,
        "exam_score": 100,
        "engagement_score": 100,
    }

    assert calculate_performance_score(student) == 100.0


def test_zero_performance_score():
    """A student with zero scores should receive zero."""

    student = {
        "attendance": 0,
        "assignment_score": 0,
        "exam_score": 0,
        "engagement_score": 0,
    }

    assert calculate_performance_score(student) == 0.0


def test_scores_are_clamped():
    """Values outside the 0–100 range should be clamped."""

    student = {
        "attendance": 120,
        "assignment_score": -10,
        "exam_score": 100,
        "engagement_score": 50,
    }

    score = calculate_performance_score(student)

    assert score == 67.5


def test_missing_values_use_defaults():
    """Missing metrics should default to zero."""

    student = {}

    assert calculate_performance_score(student) == 0.0


def test_invalid_values_use_defaults():
    """Invalid numeric values should default to zero."""

    student = {
        "attendance": "invalid",
        "assignment_score": None,
        "exam_score": 50,
        "engagement_score": 50,
    }

    assert calculate_performance_score(student) == 27.5


@pytest.mark.parametrize(
    "score, expected_level",
    [
        (90, "Excellent"),
        (85, "Excellent"),
        (75, "Good"),
        (70, "Good"),
        (60, "Average"),
        (50, "Average"),
        (40, "Needs Improvement"),
        (0, "Needs Improvement"),
    ],
)
def test_performance_level_classification(score, expected_level):
    """Test performance level boundaries."""

    student = {
        "attendance": score,
        "assignment_score": score,
        "exam_score": score,
        "engagement_score": score,
    }

    result = calculate_student_metrics(student)

    assert result["performance_score"] == score
    assert result["performance_level"] == expected_level


def test_performance_score_is_rounded():
    """Verify that calculated scores use two decimal places."""

    student = {
        "attendance": 83.33,
        "assignment_score": 72.22,
        "exam_score": 91.11,
        "engagement_score": 64.44,
    }

    score = calculate_performance_score(student)

    assert isinstance(score, float)
    assert round(score, 2) == score