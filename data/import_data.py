"""
CampusIQ student CSV import module.
"""

import csv
from pathlib import Path

from analytics.risk import calculate_risk_score, classify_risk
from analytics.scoring import calculate_performance_score
from analytics.segmentation import segment_student


REQUIRED_COLUMNS = [
    "student_id",
    "name",
    "attendance",
    "assignment_score",
    "exam_score",
    "engagement_score",
]

OPTIONAL_COLUMNS = [
    "email",
    "department",
    "year",
    "semester",
    "study_hours",
]


def _parse_float(value, field_name, row_number):
    """Convert a CSV value to a valid float."""

    try:
        number = float(value)

        if number != number or abs(number) == float("inf"):
            raise ValueError

        return number

    except (TypeError, ValueError):
        raise ValueError(
            f"Row {row_number}: Invalid numeric value "
            f"for '{field_name}'."
        )


def _parse_integer(value, field_name, row_number):
    """Convert a CSV value to an integer."""

    try:
        number = float(value)

        if (
            number != number
            or abs(number) == float("inf")
            or not number.is_integer()
        ):
            raise ValueError

        return int(number)

    except (TypeError, ValueError):
        raise ValueError(
            f"Row {row_number}: Invalid integer value "
            f"for '{field_name}'."
        )


def validate_student_record(row, row_number):
    """
    Validate and normalize one CSV student record.

    Returns:
        A dictionary containing validated student data
        and calculated metrics.
    """

    student = {}

    # Validate required text fields.
    for field in ("student_id", "name"):
        value = (row.get(field) or "").strip()

        if not value:
            raise ValueError(
                f"Row {row_number}: '{field}' cannot be empty."
            )

        student[field] = value

    # Validate required numeric fields.
    numeric_fields = [
        "attendance",
        "assignment_score",
        "exam_score",
        "engagement_score",
    ]

    for field in numeric_fields:
        value = _parse_float(
            row.get(field),
            field,
            row_number
        )

        if not 0 <= value <= 100:
            raise ValueError(
                f"Row {row_number}: '{field}' must be "
                "between 0 and 100."
            )

        student[field] = value

    # Normalize optional text fields.
    for field in ("email", "department"):
        student[field] = (row.get(field) or "").strip() or None

    # Normalize optional integer fields.
    for field, minimum, maximum in (
        ("year", 1, 4),
        ("semester", 1, 8),
    ):
        value = (row.get(field) or "").strip()

        if value:
            parsed = _parse_integer(value, field, row_number)

            if not minimum <= parsed <= maximum:
                raise ValueError(
                    f"Row {row_number}: '{field}' must be "
                    f"between {minimum} and {maximum}."
                )

            student[field] = parsed
        else:
            student[field] = None

    # Normalize study hours.
    study_hours = (row.get("study_hours") or "").strip()

    if study_hours:
        parsed_hours = _parse_float(
            study_hours,
            "study_hours",
            row_number
        )

        if parsed_hours < 0:
            raise ValueError(
                f"Row {row_number}: study_hours cannot be negative."
            )

        student["study_hours"] = parsed_hours
    else:
        student["study_hours"] = 0.0

    # Calculate derived analytics.
    student["performance_score"] = calculate_performance_score(
        student
    )

    student["risk_score"] = calculate_risk_score(student)

    student["risk_level"] = classify_risk(
        student["risk_score"]
    )

    student["segment"] = segment_student(student)

    return student


def import_students_from_csv(file_path):
    """
    Import and validate student records from a CSV file.

    Args:
        file_path: Path to the input CSV file.

    Returns:
        A list of validated student dictionaries.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the CSV structure or data is invalid.
    """

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"CSV file not found: {path}"
        )

    students = []
    seen_student_ids = set()

    try:
        with path.open(
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as csv_file:

            reader = csv.DictReader(csv_file)

            if not reader.fieldnames:
                raise ValueError("The CSV file is empty.")

            # Normalize column names.
            reader.fieldnames = [
                name.strip().lower()
                for name in reader.fieldnames
                if name
            ]

            missing_columns = [
                column
                for column in REQUIRED_COLUMNS
                if column not in reader.fieldnames
            ]

            if missing_columns:
                raise ValueError(
                    "Missing required CSV columns: "
                    + ", ".join(missing_columns)
                )

            for row_number, row in enumerate(reader, start=2):
                if not row or all(
                    not str(value or "").strip()
                    for value in row.values()
                ):
                    continue

                # Normalize keys and values.
                normalized_row = {
                    str(key).strip().lower(): value
                    for key, value in row.items()
                    if key is not None
                }

                student = validate_student_record(
                    normalized_row,
                    row_number
                )

                student_id = student["student_id"]

                if student_id in seen_student_ids:
                    raise ValueError(
                        f"Row {row_number}: Duplicate student_id "
                        f"'{student_id}'."
                    )

                seen_student_ids.add(student_id)
                students.append(student)

    except UnicodeDecodeError as exc:
        raise ValueError(
            "Unable to read the CSV file. "
            "Save it using UTF-8 encoding."
        ) from exc

    return students


def import_students_from_csv_text(csv_text):
    """
    Import records from CSV text without creating a file.
    """

    import io

    if not csv_text or not csv_text.strip():
        raise ValueError("The CSV content is empty.")

    students = []
    seen_student_ids = set()

    reader = csv.DictReader(io.StringIO(csv_text))

    if not reader.fieldnames:
        raise ValueError("The CSV file has no header row.")

    reader.fieldnames = [
        name.strip().lower()
        for name in reader.fieldnames
        if name
    ]

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in reader.fieldnames
    ]

    if missing_columns:
        raise ValueError(
            "Missing required CSV columns: "
            + ", ".join(missing_columns)
        )

    for row_number, row in enumerate(reader, start=2):
        if not row or all(
            not str(value or "").strip()
            for value in row.values()
        ):
            continue

        normalized_row = {
            str(key).strip().lower(): value
            for key, value in row.items()
            if key is not None
        }

        student = validate_student_record(
            normalized_row,
            row_number
        )

        student_id = student["student_id"]

        if student_id in seen_student_ids:
            raise ValueError(
                f"Row {row_number}: Duplicate student_id "
                f"'{student_id}'."
            )

        seen_student_ids.add(student_id)
        students.append(student)

    return students