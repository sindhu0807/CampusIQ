"""
CampusIQ Student Intervention Module.

Generates personalized interventions for student records.
Supports dictionaries and SQLAlchemy model instances.
"""

from analytics.student_utils import get_student_value


def _to_float(value, default=0.0):
    """Convert a value to float safely."""
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
    """Clamp a numeric value to a valid percentage."""
    return max(minimum, min(maximum, value))


def _value(student, field, default=0.0):
    """Read a value from a dictionary or Student model."""
    aliases = {
        "engagement": ("engagement_score",),
        "engagement_score": ("engagement",),
        "academic_score": ("exam_score", "assignment_score"),
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


def _student_scores(student):
    """Extract student performance indicators."""
    return {
        "attendance": _clamp(
            _to_float(_value(student, "attendance"))
        ),
        "academic_score": _clamp(
            _to_float(_value(student, "academic_score"))
        ),
        "engagement_score": _clamp(
            _to_float(_value(student, "engagement_score"))
        ),
        "skills_score": _clamp(
            _to_float(_value(student, "skills_score"))
        ),
        "placement_readiness": _clamp(
            _to_float(_value(student, "placement_readiness"))
        ),
    }


def generate_interventions(student):
    """
    Generate actionable recommendations based on student weaknesses.

    Returns a list of dictionaries containing title, priority,
    description, and action.
    """
    scores = _student_scores(student)
    interventions = []

    if scores["attendance"] < 75:
        interventions.append({
            "title": "Improve Attendance",
            "priority": "High",
            "description": (
                "Review attendance patterns and help the student "
                "develop a consistent class attendance routine."
            ),
            "action": "Create a weekly attendance plan.",
        })

    if scores["academic_score"] < 50:
        interventions.append({
            "title": "Academic Support",
            "priority": "High",
            "description": (
                "Identify academic learning gaps and provide "
                "additional explanations or tutoring."
            ),
            "action": "Arrange a subject-wise support session.",
        })

    if scores["engagement_score"] < 40:
        interventions.append({
            "title": "Increase Engagement",
            "priority": "Medium",
            "description": (
                "Explore barriers to participation and encourage "
                "involvement in classroom or group learning."
            ),
            "action": "Arrange a student check-in.",
        })

    if scores["skills_score"] < 50:
        interventions.append({
            "title": "Technical Skills Development",
            "priority": "High",
            "description": (
                "Identify technical skill gaps and provide "
                "structured practice opportunities."
            ),
            "action": "Create a technical skills practice plan.",
        })

    if scores["placement_readiness"] < 50:
        interventions.append({
            "title": "Placement Preparation",
            "priority": "High",
            "description": (
                "Help the student strengthen interview preparation, "
                "aptitude, resume quality, and technical readiness."
            ),
            "action": "Schedule a placement preparation session.",
        })

    if not interventions:
        interventions.append({
            "title": "Maintain Progress",
            "priority": "Low",
            "description": (
                "Continue monitoring academic performance, "
                "engagement, and placement preparation."
            ),
            "action": "Review progress during the next assessment.",
        })

    return interventions


def build_recommendations(student):
    """
    Compatibility wrapper for the function used by app.py.
    """
    return generate_interventions(student)