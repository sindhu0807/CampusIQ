"""
CampusIQ student segmentation module.
"""

from analytics.student_utils import get_student_value


def _to_float(value, default=0.0):
    """Convert a value to float safely."""
    try:
        number = float(value)

        if number != number or abs(number) == float("inf"):
            return default

        return number

    except (TypeError, ValueError, OverflowError):
        return default


def _clamp(value, minimum=0.0, maximum=100.0):
    """Keep a value within the specified range."""
    return max(minimum, min(maximum, value))


def _student_score(student, field, default=0.0):
    """Read and normalize a score from a dictionary or model."""
    value = get_student_value(student, field, default)
    return _clamp(_to_float(value, default))


def segment_student(student):
    """
    Assign a student to an academic segment.

    Supports dictionaries and SQLAlchemy Student objects.

    Returns:
        A segment name as a string.
    """

    attendance = _student_score(student, "attendance")
    assignment_score = _student_score(student, "assignment_score")
    exam_score = _student_score(student, "exam_score")
    engagement_score = _student_score(student, "engagement_score")

    # Newer CampusIQ indicators.
    academic_score = _student_score(student, "academic_score")
    skills_score = _student_score(student, "skills_score")
    placement_readiness = _student_score(
        student, "placement_readiness"
    )

    # Use newer academic data when legacy assessment fields
    # are unavailable or contain their default value.
    if academic_score > 0 and exam_score == 0:
        exam_score = academic_score

    performance_score = (
        attendance * 0.20
        + assignment_score * 0.25
        + exam_score * 0.40
        + engagement_score * 0.15
    )

    # Students with strong overall results.
    if performance_score >= 85 and attendance >= 75:
        return "High Performers"

    # Students whose academic results need attention.
    if performance_score < 50 or exam_score < 40:
        return "Needs Support"

    # Students with inconsistent participation or attendance.
    if attendance < 75 or engagement_score < 40:
        return "Low Engagement"

    # Students performing at a moderate level.
    if performance_score < 70:
        return "Developing Learners"

    return "Consistent Learners"


def _student_to_dict(student):
    """Convert a student dictionary or model into a plain dictionary."""
    if isinstance(student, dict):
        return student.copy()

    if hasattr(student, "__table__"):
        return {
            column.name: getattr(student, column.name)
            for column in student.__table__.columns
        }

    if hasattr(student, "__dict__"):
        return {
            key: value
            for key, value in vars(student).items()
            if not key.startswith("_")
        }

    return {}


def segment_students(students):
    """
    Assign segments to multiple students.

    Returns:
        A list of dictionaries containing student data and segment.
    """
    results = []

    for student in students:
        student_data = _student_to_dict(student)
        student_data["segment"] = segment_student(student)
        results.append(student_data)

    return results


def get_segment_summary(students):
    """
    Count the number of students in each segment.

    Returns:
        A dictionary mapping segment names to student counts.
    """
    summary = {}

    for student in students:
        segment = segment_student(student)
        summary[segment] = summary.get(segment, 0) + 1

    return summary


def segment_for_student(student):
    """Compatibility wrapper for the application's segmentation import."""
    return segment_student(student)