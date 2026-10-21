import os
import pandas as pd
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from functools import wraps
from db_connection import get_connection

from dotenv import load_dotenv
from flask import (
    Flask, jsonify, render_template,
    request, redirect, url_for, session
)

from analysis import (
    get_placement_rate,
    get_department_report,
    get_package_summary,
    get_skill_demand,
    get_role_analysis,
    get_department_package_analysis
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

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Check the admin account first
        admin_username = os.getenv("PLACEMENT_USERNAME")
        admin_password = os.getenv("PLACEMENT_PASSWORD")

        if (
            admin_username
            and admin_password
            and username == admin_username
            and password == admin_password
        ):
            session.clear()
            session["logged_in"] = True
            session["role"] = "admin"
            session["username"] = username
            return redirect(url_for("dashboard"))

        # Check registered student accounts
        conn = None
        cursor = None

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT user_id, full_name, username, password_hash
                FROM student_accounts
                WHERE username = %s
                """,
                (username,)
            )

            student = cursor.fetchone()

            if student and check_password_hash(
                student["password_hash"], password
            ):
                session.clear()
                session["logged_in"] = True
                session["role"] = "student"
                session["user_id"] = student["user_id"]
                session["full_name"] = student["full_name"]
                session["username"] = student["username"]
                return redirect(url_for("dashboard"))

        except Exception:
            app.logger.exception("Login database check failed")
            error = "Unable to check your account. Please try again."

        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

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

    if not full_name or not email or not username or not password:
        return render_template(
            "register.html",
            error="Please fill in all fields."
        )

    if len(password) < 8:
        return render_template(
            "register.html",
            error="Password must contain at least 8 characters."
        )

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(buffered=True)

        cursor.execute(
            """
            SELECT user_id
            FROM student_accounts
            WHERE email = %s OR username = %s
            LIMIT 1
            """,
            (email, username)
        )

        existing_account = cursor.fetchone()

        if existing_account:
            return render_template(
                "register.html",
                error="That email or username is already registered."
            )

        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO student_accounts
                (full_name, email, username, password_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (full_name, email, username, password_hash)
        )

        conn.commit()
        return redirect("/login", code=303)

    except Exception as e:
        if conn:
             conn.rollback()

        app.logger.exception("Student registration failed")

        return render_template(
            "register.html",
            error=f"Registration failed: {str(e)}"
    )
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def get_department_package_analysis():
    conn = get_connection()

    query = """
        SELECT
            s.department AS department,
            ROUND(AVG(p.package_lpa), 2) AS average_package_lpa,
            COUNT(p.placement_id) AS placement_count
        FROM students s
        JOIN placements p
            ON s.student_id = p.student_id
        WHERE p.status = 'PLACED'
          AND p.package_lpa IS NOT NULL
        GROUP BY s.department
        ORDER BY average_package_lpa DESC
    """

    try:
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("index.html")


@app.route("/api/summary")
@login_required
def summary():
    return jsonify({
        "placement": get_placement_rate(),
        "package": get_package_summary()
    })


@app.route("/api/departments")
@login_required
def departments():
    df = get_department_report()
    return jsonify(df.to_dict(orient="records"))


@app.route("/api/skills")
@login_required
def skills():
    df = get_skill_demand()
    return jsonify(df.to_dict(orient="records"))


@app.route("/api/roles")
@login_required
def roles():
    df = get_role_analysis()
    return jsonify(df.to_dict(orient="records"))


@app.route("/api/department-packages")
@login_required
def department_packages():
    df = get_department_package_analysis()
    return jsonify(df.to_dict(orient="records"))



if __name__ == "__main__":
    app.run(debug=True)