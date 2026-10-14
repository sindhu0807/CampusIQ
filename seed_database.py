"""
Populate CampusIQ with sample student records.
"""

import random

from app import app
from database.db import db
from database.models import Student


DEPARTMENTS = [
    "Computer Science",
    "Artificial Intelligence",
    "Information Technology",
    "Electronics",
    "Mechanical Engineering",
    "Electrical Engineering",
]


def seed_database(count=100):
    with app.app_context():

        existing_count = Student.query.count()

        if existing_count > 0:
            print(f"Database already contains {existing_count} students.")
            print("No records were added to avoid duplicates.")
            return

        random.seed(42)

        try:
            for number in range(1, count + 1):

                # Generate scores BEFORE creating the student
                academic_score = round(random.uniform(35, 98), 2)
                attendance = round(random.uniform(45, 100), 2)
                lms_activity = round(random.uniform(20, 100), 2)
                engagement = round(random.uniform(30, 100), 2)
                skills_score = round(random.uniform(25, 98), 2)
                placement_readiness = round(random.uniform(20, 100), 2)
                study_hours = round(random.uniform(1, 8), 2)

                student = Student(
                    student_id=f"CAMPUS{number:04d}",
                    name=f"Student {number:03d}",
                    email=f"student{number}@campusiq.demo",
                    department=DEPARTMENTS[
                        (number - 1) % len(DEPARTMENTS)
                    ],
                    year=random.randint(1, 4),
                    semester=random.randint(1, 8),

                    # Existing model fields
                    attendance=attendance,
                    assignment_score=academic_score,
                    exam_score=academic_score,
                    study_hours=study_hours,
                    engagement_score=engagement,

                    # Newer analysis fields
                    academic_score=academic_score,
                    lms_activity=lms_activity,
                    skills_score=skills_score,
                    placement_readiness=placement_readiness,
                )

                db.session.add(student)

            db.session.commit()

            print(f"Successfully added {count} demo students.")
            print(f"Total student records: {Student.query.count()}")

            print("\nDepartment distribution:")
            for department in DEPARTMENTS:
                total = Student.query.filter_by(
                    department=department
                ).count()
                print(f"{department}: {total}")

        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    seed_database()