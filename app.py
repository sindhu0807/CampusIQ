import csv
import io
import os
from functools import wraps
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from config import Config

from database.db import db
from database.models import Student, User, AnalysisHistory

from analytics.scoring import (
    calculate_performance_score,
    score_breakdown,
    valid_score,
)

from analytics.risk import risk_flags
from analytics.segmentation import segment_for_student

from agents.agents import analyze_student
from agents.interventions import build_recommendations
from agents.explainability import explain_analysis


# ==================================================
# APPLICATION CONFIGURATION
# ==================================================

load_dotenv()

app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static",
    template_folder="templates",
)

app.config.from_object(Config)

# Never expose detailed exception messages to end users.
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

db.init_app(app)


# ==================================================
# CONSTANTS
# ==================================================

ANALYSIS_FIELDS = (
    "academic_score",
    "attendance",
    "lms_activity",
    "engagement",
    "skills_score",
    "placement_readiness",
)

FIELD_LABELS = {
    "academic_score": "Academic score",
    "attendance": "Attendance",
    "lms_activity": "LMS activity",
    "engagement": "Engagement",
    "skills_score": "Technical skills",
    "placement_readiness": "Placement readiness",
}

ALLOWED_DEPARTMENTS = {
    "Computer Science",
    "Artificial Intelligence",
    "Information Technology",
    "Electronics",
    "Mechanical Engineering",
    "Electrical Engineering",
}


# ==================================================
# COMPATIBILITY HELPERS
# ==================================================

def get_student_value(student, field, default=None):
    """
    Read a value from a SQLAlchemy Student object or dictionary.

    The engagement field is compatible with the model's
    engagement_score attribute.
    """

    aliases = {
        "engagement": "engagement_score",
        "engagement_score": "engagement",
        "lms_activity": "lms_activity",
        "placement_readiness": "placement_readiness",
    }

    if isinstance(student, dict):
        if field in student:
            return student[field]

        alias = aliases.get(field)

        if alias and alias in student:
            return student[alias]

        return default

    value = getattr(student, field, None)

    if value is not None:
        return value

    alias = aliases.get(field)

    if alias:
        value = getattr(student, alias, None)

        if value is not None:
            return value

    return default


def normalize_department(value):
    """
    Normalize a department while preserving its canonical name.

    Matching is case-insensitive, but the returned value uses
    the exact department name configured in ALLOWED_DEPARTMENTS.
    """

    if not value:
        return None

    normalized = str(value).strip().casefold()

    for department in ALLOWED_DEPARTMENTS:
        if department.casefold() == normalized:
            return department

    # Optional aliases for CSV files or older forms.
    aliases = {
        "cse": "Computer Science",
        "cs": "Computer Science",
        "aiml": "Artificial Intelligence",
        "ai/ml": "Artificial Intelligence",
        "ai": "Artificial Intelligence",
        "it": "Information Technology",
        "ece": "Electronics",
        "mech": "Mechanical Engineering",
        "eee": "Electrical Engineering",
    }

    return aliases.get(normalized)


def student_model_values(values):
    """
    Convert form/CSV field names into Student model attributes.

    Do not pass the form-only 'engagement' keyword into the
    Student model when the model uses 'engagement_score'.
    """

    result = {}

    for field in ANALYSIS_FIELDS:
        value = values[field]

        if field == "engagement":
            result["engagement_score"] = value
        else:
            result[field] = value

    return result


def safe_next_url(target):
    """
    Accept only local redirect targets.
    """

    if not target:
        return None

    parsed = urlparse(target)

    if parsed.scheme or parsed.netloc:
        return None

    if not target.startswith("/") or target.startswith("//"):
        return None

    return target


# ==================================================
# AUTHENTICATION DECORATOR
# ==================================================

def login_required(view):
    """
    Require an authenticated user before accessing a route.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not session.get("user_id"):
            flash(
                "Please log in to access that page.",
                "warning",
            )

            return redirect(
                url_for(
                    "login",
                    next=request.path,
                )
            )

        return view(*args, **kwargs)

    return wrapped


# ==================================================
# STUDENT PROCESSING
# ==================================================

def student_row(student):
    """
    Prepare calculated information for a student.
    """

    score = calculate_performance_score(student)

    flags = risk_flags(student)

    segment = segment_for_student(student)

    actions = build_recommendations(student)

    return {
        "student": student,
        "score": score,
        "segment": segment,
        "flags": flags,
        "reasons": (
            flags.get("academic_reasons", [])
            + flags.get("placement_reasons", [])
        ),
        "actions": actions,
    }


def average_field(students, field):
    """
    Calculate an indicator average, excluding invalid values.
    """

    values = []

    for student in students:
        value = get_student_value(student, field)

        if valid_score(value):
            values.append(float(value))

    if not values:
        return None

    return round(sum(values) / len(values), 1)


# ==================================================
# DASHBOARD METRICS
# ==================================================

def dashboard_metrics(students):
    """
    Calculate the statistics displayed on the dashboard.
    """

    scores = [
        calculate_performance_score(student)
        for student in students
    ]

    valid_scores = [
        score
        for score in scores
        if score is not None
    ]

    flags_list = [
        risk_flags(student)
        for student in students
    ]

    academic_risk_count = sum(
        bool(flags.get("academic_risk", False))
        for flags in flags_list
    )

    placement_risk_count = sum(
        bool(flags.get("placement_risk", False))
        for flags in flags_list
    )

    high_risk_count = sum(
        bool(
            flags.get("academic_risk", False)
            or flags.get("placement_risk", False)
        )
        for flags in flags_list
    )

    high_performers = sum(
        score is not None and score >= 80
        for score in scores
    )

    chart_labels = [
        "Academic",
        "Attendance",
        "LMS Activity",
        "Engagement",
        "Skills",
        "Placement",
    ]

    chart_values = [
        average_field(students, field)
        for field in ANALYSIS_FIELDS
    ]

    average_score = (
        round(sum(valid_scores) / len(valid_scores), 1)
        if valid_scores
        else 0
    )

    return {
        "total": len(students),
        "avg_score": average_score,
        "academic_risk_count": academic_risk_count,
        "placement_risk_count": placement_risk_count,
        "high_risk_count": high_risk_count,
        "high_performers": high_performers,
        "chart": {
            "labels": chart_labels,
            "values": chart_values,
        },
    }


# ==================================================
# MAIN DASHBOARD
# ==================================================

@app.route("/")
def dashboard():

    students = (
        Student.query
        .order_by(Student.id.desc())
        .all()
    )

    metrics = dashboard_metrics(students)

    rows = [
        student_row(student)
        for student in students[:8]
    ]

    recent_history = (
        AnalysisHistory.query
        .order_by(AnalysisHistory.created_at.desc())
        .limit(4)
        .all()
    )

    activities = []

    for item in recent_history:

        readiness = getattr(
            item,
            "readiness_score",
            None,
        )

        readiness_text = (
            f"{readiness:.1f}%"
            if readiness is not None
            else "Not available"
        )

        activities.append({
            "title": (
                f"Assessment saved · "
                f"{item.department}"
            ),
            "detail": (
                f"Year {item.year} · "
                f"readiness {readiness_text}"
            ),
            "when": (
                item.created_at.strftime("%d %b, %I:%M %p")
                if item.created_at
                else "Recently"
            ),
        })

    if not activities:
        activities = [
            {
                "title": "CampusIQ is ready",
                "detail": (
                    "Import or generate student records "
                    "to begin."
                ),
                "when": "Now",
            }
        ]

    return render_template(
        "dashboard.html",
        **metrics,
        rows=rows,
        activities=activities,
        current_user=session.get("user_name"),
    )


# ==================================================
# STUDENT DIRECTORY
# ==================================================

@app.route("/students")
def students():

    all_students = (
        Student.query
        .order_by(Student.name.asc())
        .all()
    )

    rows = [
        student_row(student)
        for student in all_students
    ]

    departments = sorted({
        student.department
        for student in all_students
        if student.department
    })

    return render_template(
        "students.html",
        rows=rows,
        departments=departments,
    )


# ==================================================
# INDIVIDUAL STUDENT PROFILE
# ==================================================

@app.route("/students/<int:student_id>")
def student_detail(student_id):

    student = db.session.get(Student, student_id)

    if student is None:
        flash(
            "Student record not found.",
            "warning",
        )

        return redirect(url_for("students"))

    row = student_row(student)

    score = row["score"]
    breakdown = score_breakdown(student)
    flags = row["flags"]

    analysis = analyze_student(student)

    explanation = explain_analysis(
        student,
        score,
        breakdown,
        flags,
    )

    return render_template(
        "student_detail.html",
        student=student,
        score=score,
        breakdown=breakdown,
        flags=flags,
        segment=row["segment"],
        actions=row["actions"],
        explanation=explanation,
        analysis=analysis,
    )


# ==================================================
# PERFORMANCE ANALYTICS
# ==================================================

@app.route("/analytics")
def analytics():

    students_list = Student.query.all()

    metrics = dashboard_metrics(students_list)

    department_stats = []

    departments = sorted({
        student.department
        for student in students_list
        if student.department
    })

    for department in departments:

        subset = [
            student
            for student in students_list
            if student.department == department
        ]

        scores = [
            calculate_performance_score(student)
            for student in subset
        ]

        scores = [
            score
            for score in scores
            if score is not None
        ]

        average = (
            round(sum(scores) / len(scores), 1)
            if scores
            else 0
        )

        department_stats.append({
            "department": department,
            "count": len(subset),
            "average": average,
        })

    return render_template(
        "analytics.html",
        count=metrics["total"],
        avg_score=metrics["avg_score"],
        academic_risk_count=metrics["academic_risk_count"],
        placement_risk_count=metrics["placement_risk_count"],
        labels=metrics["chart"]["labels"],
        values=metrics["chart"]["values"],
        department_stats=department_stats,
    )


# ==================================================
# RISK MONITORING
# ==================================================

@app.route("/risk")
def risk_students():
    students_list = Student.query.all()

    rows = []

    for student in students_list:
        row = student_row(student)
        flags = row.get("flags", {})

        academic_risk = bool(flags.get("academic_risk", False))
        placement_risk = bool(flags.get("placement_risk", False))

        if academic_risk or placement_risk:
            row["risk_type"] = (
                "Academic & Placement"
                if academic_risk and placement_risk
                else "Academic"
                if academic_risk
                else "Placement"
            )
            rows.append(row)

    rows.sort(
        key=lambda row: (
            -(row["flags"].get("risk_score", 0) or 0),
            row["score"] if row["score"] is not None else -1,
        )
    )

    return render_template(
        "risk.html",
        rows=rows,
        total_students=len(students_list),
        at_risk_count=len(rows),
    )
# ==================================================
# STUDENT SEGMENTATION
# ==================================================

@app.route("/segments")
def segments():

    rows = [
        student_row(student)
        for student in Student.query.all()
    ]

    grouped = {}

    for row in rows:
        grouped.setdefault(row["segment"], []).append(row)

    summary = []

    for name, members in sorted(grouped.items()):

        scores = [
            row["score"]
            for row in members
            if row["score"] is not None
        ]

        average_score = (
            round(sum(scores) / len(scores), 1)
            if scores
            else 0
        )

        summary.append({
            "name": name,
            "count": len(members),
            "average_score": average_score,
        })

    return render_template(
        "segments.html",
        rows=rows,
        summary=summary,
        total=len(rows),
    )


# ==================================================
# PERSONALIZED RECOMMENDATIONS
# ==================================================

@app.route("/recommendations")
def recommendations():

    results = [
        student_row(student)
        for student in Student.query.all()
    ]

    results.sort(
        key=lambda row: (
            -len(row["actions"]),
            (
                row["score"]
                if row["score"] is not None
                else -1
            ),
        )
    )

    return render_template(
        "recommendations.html",
        recommendations=results,
    )


# ==================================================
# AI INSIGHTS
# ==================================================

@app.route("/ai-insights")
def ai_insights():

    students_list = Student.query.all()

    metrics = dashboard_metrics(students_list)

    rows = [
        student_row(student)
        for student in students_list
    ]

    weakest = []

    for field, label in zip(
        ANALYSIS_FIELDS,
        metrics["chart"]["labels"],
    ):

        value = average_field(students_list, field)

        weakest.append({
            "label": label,
            "value": value,
        })

    weakest.sort(
        key=lambda item: (
            item["value"]
            if item["value"] is not None
            else float("inf")
        )
    )

    insights = []

    if not students_list:

        insights.append({
            "title": "No student data yet",
            "detail": (
                "Import a CSV or generate demo records "
                "to see campus-level insights."
            ),
            "kind": "info",
        })

    else:

        if metrics["academic_risk_count"]:
            insights.append({
                "title": (
                    f"{metrics['academic_risk_count']} "
                    "students flagged for academic review"
                ),
                "detail": (
                    "Review each flag and agree on support "
                    "actions with the student."
                ),
                "kind": "risk",
            })

        if metrics["placement_risk_count"]:
            insights.append({
                "title": (
                    f"{metrics['placement_risk_count']} "
                    "students flagged for placement support"
                ),
                "detail": (
                    "Consider technical-skills practice, "
                    "aptitude preparation, resume feedback, "
                    "and mock interviews."
                ),
                "kind": "placement",
            })

        lowest_indicator = next(
            (
                item
                for item in weakest
                if item["value"] is not None
            ),
            None,
        )

        if lowest_indicator:
            insights.append({
                "title": (
                    f"{lowest_indicator['label']} "
                    "is the lowest campus average"
                ),
                "detail": (
                    f"The current average is "
                    f"{lowest_indicator['value']}%. "
                    "Review this signal alongside "
                    "the underlying student records."
                ),
                "kind": "trend",
            })

        if not insights:
            insights.append({
                "title": "No current threshold flags",
                "detail": (
                    "Continue monitoring performance "
                    "and review data quality regularly."
                ),
                "kind": "success",
            })

    return render_template(
        "ai_insights.html",
        metrics=metrics,
        weakest=weakest,
        insights=insights,
        rows=rows[:8],
    )


# ==================================================
# INSTANT STUDENT ANALYSIS
# ==================================================

@app.route("/analyze", methods=["GET", "POST"])
def student_analysis():

    if request.method == "GET":
        return render_template(
            "student_analysis.html",
            departments=sorted(ALLOWED_DEPARTMENTS),
            values={},
        )

    # Department: preserve canonical department spelling.
    department = normalize_department(
        request.form.get("department", "")
    )

    if department is None:
        flash(
            "Choose a valid department.",
            "warning",
        )

        return render_template(
            "student_analysis.html",
            departments=sorted(ALLOWED_DEPARTMENTS),
            values=request.form,
        ), 400

    # Academic year.
    try:
        year = int(request.form.get("year", "3"))
    except (TypeError, ValueError):
        flash(
            "Choose a valid academic year.",
            "warning",
        )

        return render_template(
            "student_analysis.html",
            departments=sorted(ALLOWED_DEPARTMENTS),
            values=request.form,
        ), 400

    if year not in (1, 2, 3, 4):
        flash(
            "Academic year must be between 1 and 4.",
            "warning",
        )

        return render_template(
            "student_analysis.html",
            departments=sorted(ALLOWED_DEPARTMENTS),
            values=request.form,
        ), 400

    # Read and validate all numeric fields.
    values = {}

    for field in ANALYSIS_FIELDS:

        raw = request.form.get(field, "").strip()

        try:
            value = float(raw)
        except (TypeError, ValueError):
            flash(
                f"{FIELD_LABELS[field]} must be a number "
                "from 0 to 100.",
                "warning",
            )

            return render_template(
                "student_analysis.html",
                departments=sorted(ALLOWED_DEPARTMENTS),
                values=request.form,
            ), 400

        if not valid_score(value):
            flash(
                f"{FIELD_LABELS[field]} must be between "
                "0 and 100.",
                "warning",
            )

            return render_template(
                "student_analysis.html",
                departments=sorted(ALLOWED_DEPARTMENTS),
                values=request.form,
            ), 400

        values[field] = value

    # Map the form's field names to actual model attributes.
    model_values = student_model_values(values)

    temporary_student = Student(
        student_id="INSTANT-ANALYSIS",
        name="Instant Analysis",
        department=department,
        year=year,
        **model_values,
    )

    # Calculate results.
    score = calculate_performance_score(temporary_student)

    breakdown = score_breakdown(temporary_student)

    flags = risk_flags(temporary_student)

    actions = build_recommendations(temporary_student)

    analysis = analyze_student(temporary_student)

    explanation = explain_analysis(
        temporary_student,
        score,
        breakdown,
        flags,
    )

    # Save only when explicitly requested by a logged-in user.
    if request.form.get("save_result") == "yes":

        if not session.get("user_id"):
            flash(
                "Log in before saving an analysis.",
                "warning",
            )

            return redirect(url_for("login"))

        history = AnalysisHistory(
            user_id=session["user_id"],
            department=department,
            year=year,
            academic_score=values["academic_score"],
            attendance=values["attendance"],
            lms_activity=values["lms_activity"],
            engagement=values["engagement"],
            skills_score=values["skills_score"],
            readiness_score=values["placement_readiness"],
        )

        try:
            db.session.add(history)
            db.session.commit()

        except Exception:
            db.session.rollback()

            app.logger.exception(
                "Could not save analysis history"
            )

            flash(
                "The analysis was calculated, but could not "
                "be saved to history.",
                "warning",
            )

        else:
            flash(
                "Analysis saved to your history.",
                "success",
            )

    return render_template(
        "analysis_result.html",
        department=department,
        year=year,
        data=values,
        score=score,
        breakdown=breakdown,
        flags=flags,
        actions=actions,
        analysis=analysis,
        explanation=explanation,
    )


# ==================================================
# USER REGISTRATION
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        email = request.form.get("email", "").strip().lower()

        password = request.form.get("password", "")

        confirm_password = request.form.get(
            "confirm_password",
            "",
        )

        if len(name) < 2 or not email or not password:
            flash(
                "Enter your name, email, and password.",
                "warning",
            )

            return render_template("register.html"), 400

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "warning",
            )

            return render_template("register.html"), 400

        if password != confirm_password:
            flash(
                "Passwords do not match.",
                "warning",
            )

            return render_template("register.html"), 400

        if User.query.filter_by(email=email).first():
            flash(
                "An account with that email already exists.",
                "warning",
            )

            return render_template("register.html"), 409

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
        )

        try:
            db.session.add(user)
            db.session.commit()

        except Exception:
            db.session.rollback()

            app.logger.exception("Registration failed")

            flash(
                "Could not create the account. Please try again.",
                "danger",
            )

            return render_template("register.html"), 500

        flash(
            "Account created. You can now sign in.",
            "success",
        )

        return redirect(url_for("login"))

    return render_template("register.html")


# ==================================================
# USER LOGIN
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if (
            user
            and check_password_hash(
                user.password_hash,
                password,
            )
        ):

            session.clear()

            session["user_id"] = user.id

            session["user_name"] = user.name

            flash(
                f"Welcome back, {user.name}.",
                "success",
            )

            next_url = safe_next_url(
                request.args.get("next")
            )

            if next_url:
                return redirect(next_url)

            return redirect(url_for("dashboard"))

        flash(
            "Invalid email or password.",
            "danger",
        )

        return render_template("login.html"), 401

    return render_template("login.html")


# ==================================================
# USER LOGOUT
# ==================================================

@app.route("/logout", methods=["POST"])
@login_required
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success",
    )

    return redirect(url_for("dashboard"))


# ==================================================
# SAVED ANALYSIS HISTORY
# ==================================================

@app.route("/history")
@login_required
def analysis_history():

    history = (
        AnalysisHistory.query
        .filter_by(user_id=session["user_id"])
        .order_by(AnalysisHistory.created_at.desc())
        .all()
    )

    return render_template(
        "history.html",
        history=history,
    )


# ==================================================
# ACCOUNT SETTINGS
# ==================================================

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    user = db.session.get(
        User,
        session["user_id"],
    )

    if user is None:
        session.clear()

        flash(
            "Your account could not be found. Please log in again.",
            "warning",
        )

        return redirect(url_for("login"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        if len(name) < 2:
            flash(
                "Name must contain at least 2 characters.",
                "warning",
            )

        else:
            user.name = name

            try:
                db.session.commit()

            except Exception:
                db.session.rollback()

                app.logger.exception(
                    "Settings update failed"
                )

                flash(
                    "Could not update settings.",
                    "danger",
                )

            else:
                session["user_name"] = name

                flash(
                    "Settings updated.",
                    "success",
                )

                return redirect(url_for("settings"))

    return render_template(
        "settings.html",
        user=user,
    )


# ==================================================
# CSV STUDENT IMPORT
# ==================================================

@app.route("/import", methods=["POST"])
@login_required
def import_students():

    upload = request.files.get("file")

    if (
        not upload
        or not upload.filename
        or not upload.filename.lower().endswith(".csv")
    ):
        flash(
            "Choose a CSV file to import.",
            "warning",
        )

        return redirect(url_for("students"))

    try:

        content = upload.stream.read().decode("utf-8-sig")

        reader = csv.DictReader(io.StringIO(content))

        required_columns = {
            "student_id",
            "name",
            "department",
            "year",
            *ANALYSIS_FIELDS,
        }

        if (
            not reader.fieldnames
            or not required_columns.issubset(
                set(reader.fieldnames)
            )
        ):
            flash(
                "CSV is missing required columns. "
                "Check the project documentation for the format.",
                "danger",
            )

            return redirect(url_for("students"))

        added = 0

        for line_number, row in enumerate(reader, start=2):

            student_id = (row.get("student_id") or "").strip()

            name = (row.get("name") or "").strip()

            department = normalize_department(
                row.get("department")
            )

            if not student_id or not name or department is None:
                raise ValueError(
                    f"Invalid ID, name, or department "
                    f"on CSV line {line_number}."
                )

            existing = Student.query.filter_by(
                student_id=student_id
            ).first()

            if existing:
                continue

            try:
                year = int(row["year"])
            except (TypeError, ValueError):
                raise ValueError(
                    f"Invalid academic year on CSV line "
                    f"{line_number}."
                )

            if year not in (1, 2, 3, 4):
                raise ValueError(
                    f"Academic year must be between 1 and 4 "
                    f"on CSV line {line_number}."
                )

            numeric_values = {}

            for field in ANALYSIS_FIELDS:

                try:
                    value = float(row[field])
                except (TypeError, ValueError):
                    raise ValueError(
                        f"{FIELD_LABELS[field]} must be numeric "
                        f"on CSV line {line_number}."
                    )

                if not valid_score(value):
                    raise ValueError(
                        f"{FIELD_LABELS[field]} must be between "
                        f"0 and 100 on CSV line {line_number}."
                    )

                numeric_values[field] = value

            model_values = student_model_values(numeric_values)

            student = Student(
                student_id=student_id,
                name=name,
                department=department,
                year=year,
                **model_values,
            )

            db.session.add(student)

            added += 1

        db.session.commit()

        flash(
            f"CSV import complete. Added {added} new student records.",
            "success",
        )

    except Exception as error:

        db.session.rollback()

        app.logger.exception("CSV import failed")

        flash(
            f"Import failed: {error}",
            "danger",
        )

    return redirect(url_for("students"))


# ==================================================
# HEALTH CHECK
# ==================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "healthy",
        "application": "CampusIQ",
    })


# ==================================================
# ERROR HANDLERS
# ==================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):

    db.session.rollback()

    app.logger.exception(
        "An unhandled server error occurred"
    )

    # Prefer a dedicated 500 template, if available.
    try:
        return render_template("500.html"), 500

    except Exception:
        return (
            "<h1>500 - Internal Server Error</h1>"
            "<p>Check the Flask terminal for the error details.</p>",
            500,
        )


# ==================================================
# DATABASE INITIALIZATION
# ==================================================

with app.app_context():
    db.create_all()


# ==================================================
# APPLICATION ENTRY POINT
# ==================================================

if __name__ == "__main__":

    app.run(
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5001")),
    )