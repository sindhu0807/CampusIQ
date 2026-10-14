"""
CampusIQ sample student data generator.
"""

import random

from analytics.risk import calculate_risk_score, classify_risk
from analytics.segmentation import segment_student
from analytics.scoring import calculate_performance_score


FIRST_NAMES = [
    "Aarav", "Aditi", "Arjun", "Ananya", "Rahul",
    "Priya", "Rohan", "Sneha", "Kiran", "Divya",
    "Vikram", "Meera", "Sai", "Kavya", "Aditya",
    "Pooja", "Nikhil", "Ishita", "Varun", "Neha",
]

LAST_NAMES = [
    "Sharma", "Reddy", "Patel", "Kumar", "Rao",
    "Verma", "Singh", "Gupta", "Naidu", "Mishra",
]

DEPARTMENTS = [
    "Computer Science",
    "Artificial Intelligence",
    "Information Technology",
    "Electronics",
    "Mechanical Engineering",
    "Electrical Engineering",
]

STUDENT_COUNT_DEFAULT = 100


def generate_student(student_number):
    """
    Generate one sample student record.

    Args:
        student_number: Unique integer used to create a student ID.

    Returns:
        A dictionary containing student academic information.
    """

    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)

    student = {
        "student_id": f"STU{student_number:04d}",
        "name": f"{first_name} {last_name}",
        "email": f"student{student_number}@example.com",
        "department": random.choice(DEPARTMENTS),
        "year": random.randint(1, 4),
        "semester": random.randint(1, 8),
        "attendance": round(random.uniform(35, 100), 2),
        "assignment_score": round(random.uniform(20, 100), 2),
        "exam_score": round(random.uniform(15, 100), 2),
        "study_hours": round(random.uniform(0, 8), 2),
        "engagement_score": round(random.uniform(10, 100), 2),
    }

    # Calculate derived metrics using the analytics modules.
    student["performance_score"] = calculate_performance_score(
        student
    )

    student["risk_score"] = calculate_risk_score(student)
    student["risk_level"] = classify_risk(student["risk_score"])

    student["segment"] = segment_student(student)

    return student


def generate_students(count=STUDENT_COUNT_DEFAULT, seed=None):
    """
    Generate multiple sample student records.

    Args:
        count: Number of students to generate.
        seed: Optional random seed for reproducible results.

    Returns:
        A list of student dictionaries.
    """

    if count < 0:
        raise ValueError("Student count cannot be negative.")

    if seed is not None:
        random.seed(seed)

    return [
        generate_student(student_number)
        for student_number in range(1, count + 1)
    ]


if __name__ == "__main__":
    import csv
    from pathlib import Path

    output_directory = Path(__file__).resolve().parent
    output_file = output_directory / "sample_students.csv"

    students = generate_students(count=100, seed=42)

    fieldnames = list(students[0].keys()) if students else []

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(students)

    print(f"Generated {len(students)} sample students.")
    print(f"CSV saved to: {output_file}")