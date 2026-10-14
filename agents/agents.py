"""
CampusIQ Student Analysis Agent.

Supports SQLAlchemy Student objects and dictionary-based student records.
Combines performance analysis, risk assessment, and recommended interventions.
"""

from analytics.student_utils import get_student_value
from analytics.scoring import calculate_performance_score, score_breakdown
from analytics.risk import risk_flags

from agents.interventions import generate_interventions
from agents.explainability import explain_performance, explain_risk


def _get(student, field, default=None):
    """Safely retrieve a student field from an object or dictionary."""
    try:
        value = get_student_value(student, field)
        if value is not None:
            return value
    except (AttributeError, KeyError, TypeError, ValueError):
        pass

    if isinstance(student, dict):
        return student.get(field, default)

    return getattr(student, field, default)


def _first_available(student, *fields, default=None):
    """Return the first available, non-empty student field."""
    for field in fields:
        value = _get(student, field)

        if value is not None and value != "":
            return value

    return default


def _safe_call(function, student, default=None):
    """Prevent an optional analysis component from crashing the whole agent."""
    try:
        result = function(student)
        return result if result is not None else default
    except (AttributeError, KeyError, TypeError, ValueError):
        return default


def analyze_student(student):
    """
    Analyze an individual student.

    Returns:
        dict: Student details, performance score, risk information,
              explanations, and recommended interventions.
    """

    if student is None:
        raise ValueError("A valid student record is required.")

    # ---------------------------------------------------------
    # 1. Identify the student
    # ---------------------------------------------------------
    student_id = _first_available(
        student,
        "student_id",
        "id",
        default=None,
    )

    student_name = _first_available(
        student,
        "name",
        "student_name",
        "full_name",
        default="Unknown Student",
    )

    # ---------------------------------------------------------
    # 2. Calculate performance score and breakdown
    # ---------------------------------------------------------
    try:
        performance_score = calculate_performance_score(student)
    except (AttributeError, KeyError, TypeError, ValueError):
        performance_score = 0

    try:
        breakdown = score_breakdown(student)
    except (AttributeError, KeyError, TypeError, ValueError):
        breakdown = {}

    if breakdown is None:
        breakdown = {}

    # ---------------------------------------------------------
    # 3. Evaluate student risk
    # ---------------------------------------------------------
    try:
        flags = risk_flags(student)
    except (AttributeError, KeyError, TypeError, ValueError):
        flags = {}

    if flags is None:
        flags = {}

    # ---------------------------------------------------------
    # 4. Generate recommended interventions
    # ---------------------------------------------------------
    interventions = _safe_call(
        generate_interventions,
        student,
        default=[],
    )

    if not isinstance(interventions, list):
        interventions = []

    # ---------------------------------------------------------
    # 5. Explain student performance
    # ---------------------------------------------------------
    performance_explanation = _safe_call(
        explain_performance,
        student,
        default={},
    )

    if not isinstance(performance_explanation, dict):
        performance_explanation = {}

    # ---------------------------------------------------------
    # 6. Explain student risk
    # ---------------------------------------------------------
    risk_explanation = _safe_call(
        explain_risk,
        student,
        default={},
    )

    if not isinstance(risk_explanation, dict):
        risk_explanation = {}

    # ---------------------------------------------------------
    # 7. Determine overall performance category
    # ---------------------------------------------------------
    try:
        numeric_score = float(performance_score)
    except (TypeError, ValueError):
        numeric_score = 0.0

    if numeric_score >= 80:
        performance_level = "Excellent"
    elif numeric_score >= 65:
        performance_level = "Good"
    elif numeric_score >= 50:
        performance_level = "Average"
    else:
        performance_level = "Needs Improvement"

    # ---------------------------------------------------------
    # 8. Collect student indicators
    # ---------------------------------------------------------
    indicators = {
        "attendance": _get(student, "attendance", 0),
        "academic_score": _first_available(
            student,
            "academic_score",
            "assignment_score",
            default=0,
        ),
        "engagement_score": _first_available(
            student,
            "engagement_score",
            "lms_activity",
            default=0,
        ),
        "skills_score": _get(student, "skills_score", 0),
        "placement_readiness": _get(
            student,
            "placement_readiness",
            0,
        ),
    }

    # ---------------------------------------------------------
    # 9. Build the final analysis result
    # ---------------------------------------------------------
    analysis = {
        "student_id": student_id,
        "student_name": student_name,
        "performance_score": round(numeric_score, 2),
        "performance_level": performance_level,
        "breakdown": breakdown,
        "risk_flags": flags,
        "risk_score": flags.get("risk_score", 0),
        "risk_level": flags.get("risk_level", "Unknown"),
        "academic_risk": flags.get("academic_risk", False),
        "placement_risk": flags.get("placement_risk", False),
        "academic_reasons": flags.get("academic_reasons", []),
        "placement_reasons": flags.get("placement_reasons", []),
        "risk_factors": flags.get("risk_factors", []),
        "interventions": interventions,
        "recommendations": interventions,
        "performance_explanation": performance_explanation,
        "risk_explanation": risk_explanation,
        "indicators": indicators,
    }

    return analysis