"""
CampusIQ student performance scoring.

Supports dictionaries and SQLAlchemy Student model instances.
"""

from analytics.student_utils import get_student_value


WEIGHTS = {
    "attendance": 0.20,
    "assignment_score": 0.25,
    "exam_score": 0.40,
    "engagement_score": 0.15,
}


def _to_float(value, default=0.0):
    """Convert a value to float, using a default for invalid values."""
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value, minimum=0.0, maximum=100.0):
    """Keep a numeric value within the specified range."""
    return max(minimum, min(maximum, value))


def _student_value(student, key, default=0.0):
    """Read a value from a dictionary or Student model."""
    return get_student_value(student, key, default)


def valid_score(value):
    """Return True if the value is a valid score between 0 and 100."""
    try:
        if value is None or value == "":
            return False

        number = float(value)
        return 0 <= number <= 100
    except (TypeError, ValueError):
        return False


def score_breakdown(student):
    """Calculate the weighted contribution of each performance metric."""
    attendance = _clamp(
        _to_float(_student_value(student, "attendance"))
    )
    assignment_score = _clamp(
        _to_float(_student_value(student, "assignment_score"))
    )
    exam_score = _clamp(
        _to_float(_student_value(student, "exam_score"))
    )
    engagement_score = _clamp(
        _to_float(_student_value(student, "engagement_score"))
    )

    breakdown = {
        "attendance": round(
            attendance * WEIGHTS["attendance"], 2
        ),
        "assignment_score": round(
            assignment_score * WEIGHTS["assignment_score"], 2
        ),
        "exam_score": round(
            exam_score * WEIGHTS["exam_score"], 2
        ),
        "engagement_score": round(
            engagement_score * WEIGHTS["engagement_score"], 2
        ),
    }

    breakdown["total"] = round(sum(breakdown.values()), 2)

    return breakdown


def calculate_performance_score(student):
    """Calculate the overall weighted performance score."""
    breakdown = score_breakdown(student)
    return round(_clamp(breakdown["total"]), 2)


def get_performance_level(score):
    """Classify a performance score into a descriptive level."""
    score = _to_float(score)

    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Average"
    else:
        return "Needs Improvement"


def calculate_student_metrics(student):
    """Return performance metrics and the overall performance level."""
    attendance = _to_float(
        _student_value(student, "attendance")
    )
    assignment_score = _to_float(
        _student_value(student, "assignment_score")
    )
    exam_score = _to_float(
        _student_value(student, "exam_score")
    )
    engagement_score = _to_float(
        _student_value(student, "engagement_score")
    )

    performance_score = calculate_performance_score(student)

    return {
        "attendance": attendance,
        "assignment_score": assignment_score,
        "exam_score": exam_score,
        "engagement_score": engagement_score,
        "performance_score": performance_score,
        "performance_level": get_performance_level(
            performance_score
        ),
        "score_breakdown": score_breakdown(student),
    }


def calculate_weighted_score(student):
    """Compatibility alias for performance scoring."""
    return calculate_performance_score(student)


def calculate_score(student):
    """Compatibility alias for performance scoring."""
    return calculate_performance_score(student)


def get_score_breakdown(student):
    """Compatibility alias for score breakdown."""
    return score_breakdown(student)