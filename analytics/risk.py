"""
CampusIQ Risk Assessment Module.

Supports current CampusIQ student fields and legacy fields.
Works with dictionaries and SQLAlchemy model instances.
"""

from analytics.student_utils import get_student_value


# Legacy risk calculation weights.
RISK_WEIGHTS = {
    "attendance": 0.30,
    "assignment_score": 0.25,
    "exam_score": 0.25,
    "engagement_score": 0.20,
}

# Thresholds for risk factors.
ACADEMIC_THRESHOLDS = {
    "attendance": 75,
    "assignment_score": 50,
    "exam_score": 50,
    "engagement_score": 40,
}

# Current CampusIQ risk calculation weights.
CURRENT_RISK_WEIGHTS = {
    "attendance": 0.25,
    "academic_score": 0.35,
    "engagement_score": 0.15,
    "skills_score": 0.15,
    "placement_readiness": 0.10,
}

CURRENT_THRESHOLDS = {
    "attendance": 75,
    "academic_score": 50,
    "engagement_score": 40,
    "skills_score": 50,
    "placement_readiness": 50,
}


def _to_float(value, default=0.0):
    """Convert a value to a finite float safely."""
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
    """Keep a numeric value within the expected range."""
    return max(minimum, min(maximum, value))


def _student_value(student, field, default=None):
    """Read a value from a dictionary or SQLAlchemy model."""
    try:
        value = get_student_value(student, field, None)
    except (AttributeError, KeyError, TypeError, ValueError):
        value = None

    if value is not None:
        return value

    if isinstance(student, dict):
        return student.get(field, default)

    return getattr(student, field, default)


def _has_value(student, field):
    """Check whether a field has a supplied value."""
    value = _student_value(student, field)
    return value is not None and value != ""


def _first_available(student, fields):
    """Return the first available value."""
    for field in fields:
        value = _student_value(student, field)

        if value is not None and value != "":
            return value

    return None


def _uses_legacy_fields(student):
    """Determine whether legacy academic fields are supplied."""
    return any(
        _has_value(student, field)
        for field in ("assignment_score", "exam_score")
    )


def _get_scores(student):
    """Extract current and legacy student indicators."""
    return {
        "attendance": _to_float(
            _student_value(student, "attendance")
        ),
        "assignment_score": _to_float(
            _student_value(student, "assignment_score")
        ),
        "exam_score": _to_float(
            _student_value(student, "exam_score")
        ),
        "academic_score": _to_float(
            _first_available(
                student,
                ("academic_score", "exam_score", "assignment_score"),
            )
        ),
        "engagement_score": _to_float(
            _first_available(
                student,
                ("engagement_score", "engagement", "lms_activity"),
            )
        ),
        "skills_score": _to_float(
            _first_available(
                student,
                ("skills_score", "technical_skills"),
            )
        ),
        "placement_readiness": _to_float(
            _first_available(
                student,
                ("placement_readiness", "readiness_score"),
            )
        ),
    }


def calculate_risk_score(student):
    """
    Calculate a weighted risk score from 0 to 100.
    Higher scores indicate greater risk.
    """
    scores = _get_scores(student)

    if _uses_legacy_fields(student):
        risk_score = (
            (100 - _clamp(scores["attendance"])) * 0.25
            + (100 - _clamp(scores["assignment_score"])) * 0.25
            + (100 - _clamp(scores["exam_score"])) * 0.30
            + (100 - _clamp(scores["engagement_score"])) * 0.20
        )
    else:
        risk_score = sum(
            (100 - _clamp(scores[field])) * weight
            for field, weight in CURRENT_RISK_WEIGHTS.items()
        )

    return round(_clamp(risk_score), 2)

def classify_risk(score):
    """Classify the risk score."""
    score = _clamp(_to_float(score))

    if score < 30:
        return "Low"

    if score < 60:
        return "Medium"

    return "High"


def get_risk_factors(student):
    """Return risk factors based on available student indicators."""
    scores = _get_scores(student)
    factors = []

    if _uses_legacy_fields(student):
        labels = {
            "attendance": "Low attendance",
            "assignment_score": "Low assignment performance",
            "exam_score": "Low examination performance",
            "engagement_score": "Low student engagement",
        }

        for field, threshold in ACADEMIC_THRESHOLDS.items():
            if not _has_value(student, field):
                continue

            value = _clamp(scores[field])

            if value < threshold:
                factors.append(labels[field])

        return factors

    labels = {
        "attendance": "Low attendance",
        "academic_score": "Low academic performance",
        "engagement_score": "Low student engagement",
        "skills_score": "Technical skills need improvement",
        "placement_readiness": "Low placement readiness",
    }

    aliases = {
        "attendance": ("attendance",),
        "academic_score": (
            "academic_score",
            "exam_score",
            "assignment_score",
        ),
        "engagement_score": (
            "engagement_score",
            "engagement",
            "lms_activity",
        ),
        "skills_score": ("skills_score", "technical_skills"),
        "placement_readiness": (
            "placement_readiness",
            "readiness_score",
        ),
    }

    for field, threshold in CURRENT_THRESHOLDS.items():
        if not any(
            _has_value(student, alias)
            for alias in aliases[field]
        ):
            continue

        if _clamp(scores[field]) < threshold:
            factors.append(labels[field])

    return factors


def assess_student_risk(student):
    """Return a complete student risk assessment."""
    risk_score = calculate_risk_score(student)
    risk_level = classify_risk(risk_score)
    risk_factors = get_risk_factors(student)

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "is_at_risk": risk_level in ("Medium", "High"),
    }


def risk_flags(student):
    """Generate the risk flags consumed by the CampusIQ application."""
    factors = get_risk_factors(student)

    academic_labels = {
        "Low attendance",
        "Low assignment performance",
        "Low examination performance",
        "Low academic performance",
        "Low student engagement",
    }

    placement_labels = {
        "Technical skills need improvement",
        "Low placement readiness",
    }

    academic_reasons = [
        factor
        for factor in factors
        if factor in academic_labels
    ]

    placement_reasons = [
        factor
        for factor in factors
        if factor in placement_labels
    ]

    risk_score = calculate_risk_score(student)

    return {
        "academic_risk": bool(academic_reasons),
        "placement_risk": bool(placement_reasons),
        "academic_reasons": academic_reasons,
        "placement_reasons": placement_reasons,
        "risk_score": risk_score,
        "risk_level": classify_risk(risk_score),
        "risk_factors": factors,
    }