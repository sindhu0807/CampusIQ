"""
CampusIQ Explainability Module.

Explains student performance and risk assessments.
Supports dictionaries and SQLAlchemy Student instances.
"""

from analytics.student_utils import get_student_value


def _to_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        if value is None or isinstance(value, bool):
            return float(default)

        result = float(value)

        if not (-float("inf") < result < float("inf")):
            return float(default)

        return result

    except (TypeError, ValueError, OverflowError):
        return float(default)


def _clamp(value, minimum=0.0, maximum=100.0):
    """Keep a score between 0 and 100."""
    return max(minimum, min(maximum, value))


def _value(student, field, default=0.0):
    """Read fields from dictionaries or Student objects."""
    aliases = {
        "academic_score": ("exam_score", "assignment_score"),
        "engagement_score": ("engagement",),
        "skills_score": ("technical_skills",),
        "placement_readiness": ("readiness_score",),
    }

    value = get_student_value(student, field, None)

    if value is not None:
        return value

    for alias in aliases.get(field, ()):
        value = get_student_value(student, alias, None)

        if value is not None:
            return value

    return default


def explain_performance(student):
    """
    Explain a student's performance using available indicators.
    Returns a dictionary of indicator values and explanations.
    """
    indicators = {
        "Attendance": _clamp(
            _to_float(_value(student, "attendance"))
        ),
        "Academic Score": _clamp(
            _to_float(_value(student, "academic_score"))
        ),
        "Engagement": _clamp(
            _to_float(_value(student, "engagement_score"))
        ),
        "Technical Skills": _clamp(
            _to_float(_value(student, "skills_score"))
        ),
        "Placement Readiness": _clamp(
            _to_float(_value(student, "placement_readiness"))
        ),
    }

    explanations = []

    for name, score in indicators.items():
        if score < 40:
            status = "Needs significant improvement"
        elif score < 60:
            status = "Needs improvement"
        elif score < 75:
            status = "Moderate"
        else:
            status = "Good"

        explanations.append({
            "indicator": name,
            "score": score,
            "status": status,
        })

    strongest = max(
        indicators,
        key=indicators.get,
    )

    weakest = min(
        indicators,
        key=indicators.get,
    )

    return {
        "indicators": indicators,
        "details": explanations,
        "strongest_indicator": strongest,
        "weakest_indicator": weakest,
        "summary": (
            f"Strongest indicator: {strongest}. "
            f"Indicator needing the most attention: {weakest}."
        ),
    }


def explain_analysis(student, score, breakdown, flags):
    """
    Explain the calculated performance score and risk assessment.
    """
    performance = explain_performance(student)

    academic_reasons = flags.get("academic_reasons", [])
    placement_reasons = flags.get("placement_reasons", [])

    if score is None:
        performance_level = "Unavailable"
    elif score >= 85:
        performance_level = "Excellent"
    elif score >= 70:
        performance_level = "Good"
    elif score >= 50:
        performance_level = "Average"
    else:
        performance_level = "Needs Improvement"

    if academic_reasons and placement_reasons:
        risk_summary = (
            "Academic and placement support may both be needed."
        )
    elif academic_reasons:
        risk_summary = (
            "Academic support may be needed."
        )
    elif placement_reasons:
        risk_summary = (
            "Placement preparation support may be needed."
        )
    else:
        risk_summary = (
            "No risk factors were identified by the current rules."
        )

    return {
        "performance_level": performance_level,
        "performance_score": score,
        "breakdown": breakdown,
        "risk_level": flags.get("risk_level", "Unknown"),
        "risk_score": flags.get("risk_score", 0),
        "academic_reasons": academic_reasons,
        "placement_reasons": placement_reasons,
        "risk_summary": risk_summary,
        "strongest_indicator": performance["strongest_indicator"],
        "weakest_indicator": performance["weakest_indicator"],
        "performance_summary": performance["summary"],
        "indicators": performance["indicators"],
    }
def explain_risk(student):
    """
    Explain academic and placement risk for a student.
    Supports dictionaries and SQLAlchemy Student instances.
    """
    from analytics.risk import risk_flags

    flags = risk_flags(student)

    academic_reasons = flags.get("academic_reasons", [])
    placement_reasons = flags.get("placement_reasons", [])

    if academic_reasons and placement_reasons:
        summary = "The student may need academic and placement support."
    elif academic_reasons:
        summary = "The student may need academic support."
    elif placement_reasons:
        summary = "The student may need placement preparation support."
    else:
        summary = "No risk factors were identified by the current rules."

    return {
        "risk_score": flags.get("risk_score", 0),
        "risk_level": flags.get("risk_level", "Unknown"),
        "academic_risk": flags.get("academic_risk", False),
        "placement_risk": flags.get("placement_risk", False),
        "academic_reasons": academic_reasons,
        "placement_reasons": placement_reasons,
        "risk_factors": flags.get("risk_factors", []),
        "summary": summary,
    }