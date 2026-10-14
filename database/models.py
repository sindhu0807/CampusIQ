from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from database.db import db


class User(db.Model):
    """Stores user accounts."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(db.Model):
    """Stores academic performance and placement-readiness data."""

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), nullable=True)

    department = db.Column(db.String(100), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    semester = db.Column(db.Integer, nullable=True)

    # Traditional academic indicators
    attendance = db.Column(db.Float, default=0.0, nullable=False)
    assignment_score = db.Column(db.Float, default=0.0, nullable=False)
    exam_score = db.Column(db.Float, default=0.0, nullable=False)
    study_hours = db.Column(db.Float, default=0.0, nullable=False)
    engagement_score = db.Column(db.Float, default=0.0, nullable=False)

    # CampusIQ performance and placement indicators
    academic_score = db.Column(db.Float, default=0.0, nullable=False)
    lms_activity = db.Column(db.Float, default=0.0, nullable=False)
    skills_score = db.Column(db.Float, default=0.0, nullable=False)
    placement_readiness = db.Column(db.Float, default=0.0, nullable=False)

    risk_score = db.Column(db.Float, default=0.0, nullable=False)
    risk_level = db.Column(db.String(30), default="Low", nullable=False)
    segment = db.Column(db.String(80), nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class AnalysisHistory(db.Model):
    """Stores saved CampusIQ assessment results."""

    __tablename__ = "analysis_history"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # Retained for compatibility with earlier analysis records
    student_id = db.Column(db.String(50), nullable=True, index=True)
    analysis_type = db.Column(
        db.String(100),
        nullable=False,
        default="Student Performance Analysis",
    )
    result = db.Column(db.Text, nullable=True)

    # Fields used by the current app.py history and analysis routes
    department = db.Column(db.String(100), nullable=True)
    year = db.Column(db.Integer, nullable=True)

    academic_score = db.Column(db.Float, default=0.0, nullable=False)
    attendance = db.Column(db.Float, default=0.0, nullable=False)
    lms_activity = db.Column(db.Float, default=0.0, nullable=False)
    engagement = db.Column(db.Float, default=0.0, nullable=False)
    skills_score = db.Column(db.Float, default=0.0, nullable=False)
    readiness_score = db.Column(db.Float, default=0.0, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user = db.relationship(
        "User",
        backref=db.backref("analysis_history", lazy=True),
    )