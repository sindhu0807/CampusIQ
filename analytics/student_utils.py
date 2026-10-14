def get_student_value(student, key, default=0):
    """Read a value from either a dictionary or a Student model."""
    if isinstance(student, dict):
        return student.get(key, default)

    return getattr(student, key, default)