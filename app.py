import os
import csv
import io
import pandas as pd
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from db_connection import get_connection
from analysis import (
    get_placement_rate, get_department_report, get_package_summary,
    get_skill_demand, get_role_analysis, get_department_package_analysis
)

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("Set FLASK_SECRET_KEY in your .env file.")

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("logged_in"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Login required"}), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view

def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("logged_in"):
                return redirect(url_for("login"))
            if session.get("role") != role:
                flash("You are not authorized to access that page.", "error")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin_username = os.getenv("PLACEMENT_USERNAME")
        admin_password = os.getenv("PLACEMENT_PASSWORD")
        if admin_username and admin_password and username == admin_username and password == admin_password:
            session.clear()
            session.update(logged_in=True, role="admin", username=username)
            return redirect(url_for("dashboard"))

        conn = cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT user_id, full_name, username, password_hash FROM student_accounts WHERE username=%s",
                (username,)
            )
            student = cursor.fetchone()
            if student and check_password_hash(student["password_hash"], password):
                session.clear()
                session.update(logged_in=True, role="student", user_id=student["user_id"],
                               full_name=student["full_name"], username=student["username"])
                return redirect(url_for("dashboard"))
        except Exception:
            app.logger.exception("Login database check failed")
            error = "Unable to check your account. Please try again."
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()
        if not error:
            error = "Invalid username or password."
    return render_template("login.html", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", error=None)
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not all([full_name, email, username, password]):
        return render_template("register.html", error="Please fill in all fields.")
    if len(password) < 8:
        return render_template("register.html", error="Password must contain at least 8 characters.")
    conn = cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM student_accounts WHERE email=%s OR username=%s LIMIT 1",
                       (email, username))
        if cursor.fetchone():
            return render_template("register.html", error="That email or username is already registered.")
        cursor.execute(
            "INSERT INTO student_accounts (full_name,email,username,password_hash) VALUES (%s,%s,%s,%s)",
            (full_name, email, username, generate_password_hash(password))
        )
        conn.commit()
        return redirect(url_for("login"), code=303)
    except Exception:
        if conn: conn.rollback()
        app.logger.exception("Student registration failed")
        return render_template("register.html", error="Registration failed. Please check the database and try again.")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

@app.route("/")
def home():
    return render_template("welcome.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("index.html")

@app.route("/student/submit", methods=["GET", "POST"])
@login_required
@role_required("student")
def student_submit():
    conn = cursor = None
    if request.method == "POST":
        roll_no = request.form.get("roll_no", "").strip().upper()
        department = request.form.get("department", "").strip()
        graduation_year = request.form.get("graduation_year", "").strip()
        skills = request.form.get("skills", "").strip()
        eligibility = request.form.get("is_eligible", "yes")
        placement_status = request.form.get("placement_status", "NOT_PLACED").strip().upper()
        company = request.form.get("company", "").strip() or None
        job_role = request.form.get("job_role", "").strip() or None
        package_raw = request.form.get("package_lpa", "").strip()
        package_lpa = None
        if package_raw:
            try:
                package_lpa = float(package_raw)
                if package_lpa < 0: raise ValueError()
            except ValueError:
                flash("Enter a valid non-negative package amount.", "error")
                return redirect(url_for("student_submit"))
        if not roll_no or not department or not graduation_year.isdigit():
            flash("Roll number, department and graduation year are required.", "error")
            return redirect(url_for("student_submit"))
        if placement_status not in {"NOT_PLACED", "APPLIED", "SELECTED", "PLACED"}:
            flash("Choose a valid placement status.", "error")
            return redirect(url_for("student_submit"))
        if placement_status == "PLACED" and (not company or not job_role):
            flash("Company and job role are required when placement status is Placed.", "error")
            return redirect(url_for("student_submit"))
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO placement_submissions
                (user_id, roll_no, department, graduation_year, is_eligible, skills,
                 placement_status, company, job_role, package_lpa, verification_status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Pending')
            """, (session["user_id"], roll_no, department, int(graduation_year),
                  eligibility == "yes", skills, placement_status, company, job_role, package_lpa))
            conn.commit()
            flash("Your details were submitted successfully and are waiting for college verification.", "success")
            return redirect(url_for("student_submit"))
        except Exception:
            if conn: conn.rollback()
            app.logger.exception("Student detail submission failed")
            flash("Submission failed. Check whether the database migration was executed.", "error")
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    submissions = []
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT submission_id, roll_no, department, graduation_year, verification_status,
                   submitted_at, placement_status
            FROM placement_submissions WHERE user_id=%s ORDER BY submitted_at DESC
        """, (session["user_id"],))
        submissions = cursor.fetchall()
    except Exception:
        app.logger.exception("Could not load student submissions")
        flash("Could not load your submission history.", "error")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return render_template("student_submit.html", submissions=submissions)

@app.route("/admin/submissions")
@login_required
@role_required("admin")
def admin_submissions():
    conn = cursor = None
    rows = []
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT ps.*, sa.full_name, sa.email
            FROM placement_submissions ps
            JOIN student_accounts sa ON sa.user_id=ps.user_id
            ORDER BY CASE WHEN ps.verification_status='Pending' THEN 0 ELSE 1 END,
                     ps.submitted_at DESC
        """)
        rows = cursor.fetchall()
    except Exception:
        app.logger.exception("Could not load submissions")
        flash("Unable to load student submissions.", "error")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return render_template("admin_submissions.html", submissions=rows)



@app.route("/admin/bulk-upload", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_bulk_upload():
    if request.method == "GET":
        return render_template("bulk_upload.html")

    file = request.files.get("file")

    if not file or not file.filename:
        flash("Please select a CSV file.", "error")
        return redirect(url_for("admin_bulk_upload"))

    if not file.filename.lower().endswith(".csv"):
        flash("Please upload a CSV file.", "error")
        return redirect(url_for("admin_bulk_upload"))

    conn = cursor = None
    inserted = 0
    duplicates = 0
    errors = []

    try:
        df = pd.read_csv(file, dtype=str, encoding="utf-8-sig")
        df.columns = df.columns.str.strip().str.lower()

        required = {
            "roll_no", "department",
            "graduation_year", "is_eligible"
        }

        if not required.issubset(df.columns):
            missing = required - set(df.columns)
            raise ValueError(
                "Missing columns: " + ", ".join(sorted(missing))
            )

        if len(df) > 5000:
            raise ValueError("Maximum 5000 rows per upload.")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        seen_rolls = set()

        for index, row in df.iterrows():
            row_number = index + 2

            def value(column):
                if column not in df.columns or pd.isna(row[column]):
                    return ""
                return str(row[column]).strip()

            try:
                roll_no = value("roll_no")
                department = value("department")
                year_text = value("graduation_year")
                eligible_text = value("is_eligible").lower()

                if not roll_no or not department or not year_text:
                    raise ValueError("Missing required student details.")

                if roll_no in seen_rolls:
                    duplicates += 1
                    continue

                seen_rolls.add(roll_no)

                year = int(year_text)
                if year < 1901 or year > 2155:
                    raise ValueError("Invalid graduation year.")

                if eligible_text in {"true", "1", "yes"}:
                    eligible = 1
                elif eligible_text in {"false", "0", "no"}:
                    eligible = 0
                else:
                    raise ValueError("is_eligible must be TRUE or FALSE.")

                skills = [
                    s.strip()
                    for s in value("skills").split(",")
                    if s.strip()
                ]

                company = value("company")
                job_role = value("job_role")
                status = value("placement_status").upper()
                package_text = value("package_lpa")

                if status and status not in {
                    "APPLIED", "SELECTED", "PLACED",
                    "REJECTED", "WITHDRAWN"
                }:
                    raise ValueError("Invalid placement status.")

                package = None
                if package_text:
                    package = float(package_text)
                    if package < 0:
                        raise ValueError("Package cannot be negative.")

                if status and (not company or not job_role):
                    raise ValueError("Company and job role are required.")

                if package is not None and not status:
                    raise ValueError("Placement status is required for a package.")

                cursor.execute("""
                    INSERT IGNORE INTO students
                    (roll_no, department, graduation_year, is_eligible)
                    VALUES (%s, %s, %s, %s)
                """, (roll_no, department, year, eligible))

                if cursor.rowcount == 0:
                    duplicates += 1
                    continue

                student_id = cursor.lastrowid

                for skill in skills:
                    cursor.execute(
                        "INSERT IGNORE INTO skills(skill_name) VALUES(%s)",
                        (skill,)
                    )
                    cursor.execute(
                        "SELECT skill_id FROM skills WHERE skill_name=%s",
                        (skill,)
                    )
                    skill_id = cursor.fetchone()["skill_id"]

                    cursor.execute("""
                        INSERT IGNORE INTO student_skills
                        (student_id, skill_id)
                        VALUES (%s, %s)
                    """, (student_id, skill_id))

                if status:
                    cursor.execute("""
                        INSERT INTO placements
                        (student_id, company, role, package_lpa,
                         placement_date, status)
                        VALUES (%s, %s, %s, %s,
                                CASE WHEN %s='PLACED'
                                     THEN CURDATE() ELSE NULL END,
                                %s)
                    """, (
                        student_id, company, job_role,
                        package, status, status
                    ))

                inserted += 1

            except (ValueError, TypeError, OverflowError) as error:
                errors.append(f"Row {row_number}: {error}")

        conn.commit()

    except Exception as error:
        if conn:
            conn.rollback()
        app.logger.exception("Bulk student upload failed")
        flash(f"Upload failed: {error}", "error")

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

    return render_template(
        "bulk_upload.html",
        inserted=inserted,
        duplicates=duplicates,
        errors=errors
    )

@app.route("/admin/submissions/<int:submission_id>/verify", methods=["POST"])
@login_required
@role_required("admin")
def verify_submission(submission_id):
    decision = request.form.get("decision")
    if decision not in {"Verified", "Rejected"}:
        flash("Invalid verification action.", "error")
        return redirect(url_for("admin_submissions"))
    conn = cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()
        cursor.execute("SELECT * FROM placement_submissions WHERE submission_id=%s FOR UPDATE",
                       (submission_id,))
        item = cursor.fetchone()
        if not item:
            conn.rollback()
            flash("Submission not found.", "error")
            return redirect(url_for("admin_submissions"))
        if item["verification_status"] != "Pending":
            conn.rollback()
            flash("This submission has already been reviewed.", "error")
            return redirect(url_for("admin_submissions"))

        if decision == "Verified":
            cursor.execute("""
                INSERT INTO students (roll_no, department, graduation_year, is_eligible)
                VALUES (%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE department=VALUES(department),
                    graduation_year=VALUES(graduation_year), is_eligible=VALUES(is_eligible)
            """, (item["roll_no"], item["department"], item["graduation_year"], item["is_eligible"]))
            cursor.execute("SELECT student_id FROM students WHERE roll_no=%s", (item["roll_no"],))
            student_id = cursor.fetchone()["student_id"]

            cursor.execute("DELETE FROM student_skills WHERE student_id=%s", (student_id,))
            skill_names = [s.strip() for s in (item["skills"] or "").split(",") if s.strip()]
            for skill in skill_names:
                cursor.execute("INSERT IGNORE INTO skills(skill_name) VALUES(%s)", (skill,))
                cursor.execute("SELECT skill_id FROM skills WHERE skill_name=%s", (skill,))
                skill_id = cursor.fetchone()["skill_id"]
                cursor.execute("INSERT IGNORE INTO student_skills(student_id,skill_id) VALUES(%s,%s)",
                               (student_id, skill_id))

            status = (item["placement_status"] or "NOT_PLACED").upper()
            if status in {"APPLIED", "SELECTED", "PLACED"} and item["company"] and item["job_role"]:
                cursor.execute("""
                    SELECT placement_id FROM placements
                    WHERE student_id=%s AND company=%s AND role=%s AND status=%s LIMIT 1
                """, (student_id, item["company"], item["job_role"], status))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO placements(student_id,company,role,package_lpa,placement_date,status)
                        VALUES(%s,%s,%s,%s,CASE WHEN %s='PLACED' THEN CURDATE() ELSE NULL END,%s)
                    """, (student_id, item["company"], item["job_role"], item["package_lpa"], status, status))

        cursor.execute("""
            UPDATE placement_submissions
            SET verification_status=%s, verified_at=NOW(), verified_by=%s
            WHERE submission_id=%s
        """, (decision, session.get("username", "admin"), submission_id))
        conn.commit()
        flash(f"Submission #{submission_id} {decision.lower()} successfully.", "success")
    except Exception:
        if conn: conn.rollback()
        app.logger.exception("Submission verification failed")
        flash("Could not process this submission. Check the database schema and try again.", "error")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return redirect(url_for("admin_submissions"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/api/summary")
@login_required
def summary():
    return jsonify({"placement": get_placement_rate(), "package": get_package_summary()})

@app.route("/api/departments")
@login_required
def departments():
    return jsonify(get_department_report().to_dict(orient="records"))

@app.route("/api/skills")
@login_required
def skills():
    return jsonify(get_skill_demand().to_dict(orient="records"))

@app.route("/api/roles")
@login_required
def roles():
    return jsonify(get_role_analysis().to_dict(orient="records"))

@app.route("/api/department-packages")
@login_required
def department_packages():
    return jsonify(get_department_package_analysis().to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)
