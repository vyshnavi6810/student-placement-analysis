import os
import csv
import io
import pandas as pd
from functools import wraps
from datetime import date
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from db_connection import get_connection
from flask import Response


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("Set FLASK_SECRET_KEY in your .env file.")

def db():
    return get_connection()

def one(cur, sql, args=()):
    cur.execute(sql, args)
    return cur.fetchone()

def all_rows(cur, sql, args=()):
    cur.execute(sql, args)
    return cur.fetchall()

def tenant_id():
    return session.get("university_id")

def login_required(fn):
    @wraps(fn)
    def wrapped(*a, **kw):
        if not session.get("logged_in") or not tenant_id():
            return redirect(url_for("home"))
        return fn(*a, **kw)
    return wrapped

def role_required(role):
    def deco(fn):
        @wraps(fn)
        @login_required
        def wrapped(*a, **kw):
            if session.get("role") != role:
                abort(403)
            return fn(*a, **kw)
        return wrapped
    return deco

def universities():
    conn=db(); cur=conn.cursor(dictionary=True)
    try: return all_rows(cur, "SELECT university_id, name, slug FROM universities WHERE is_active=1 ORDER BY name")
    finally: cur.close(); conn.close()

def selected_university():
    uid=tenant_id()
    if not uid: return None
    conn=db(); cur=conn.cursor(dictionary=True)
    try: return one(cur,"SELECT university_id,name,slug FROM universities WHERE university_id=%s AND is_active=1",(uid,))
    finally: cur.close(); conn.close()

def filters():
    return {k: request.args.get(k,"").strip() for k in ("department","graduation_year","placement_year","skill","role","company")}


def where_student(f, alias="s"):
    clauses = [f"{alias}.university_id=%s"]
    args = [tenant_id()]

    if f.get("department"):
        clauses.append(f"{alias}.department=%s")
        args.append(f["department"])

    if f.get("graduation_year"):
        clauses.append(f"{alias}.graduation_year=%s")
        args.append(f["graduation_year"])

    if f.get("skill"):
        clauses.append(f"""
            EXISTS (
                SELECT 1
                FROM student_skills ss
                JOIN skills sk
                    ON sk.skill_id = ss.skill_id
                    AND sk.university_id = ss.university_id
                WHERE ss.student_id = {alias}.student_id
                    AND ss.university_id = {alias}.university_id
                    AND sk.skill_name = %s
            )
        """)
        args.append(f["skill"])

    return " AND ".join(clauses), args

def analytics(f=None):
    f = f or {}
    conn = db()
    cur = conn.cursor(dictionary=True)

    try:
        w, args = where_student(f)

        extra = ""
        xargs = []

        if f.get("placement_year"):
            extra += " AND YEAR(p.placement_date)=%s"
            xargs.append(f["placement_year"])

        if f.get("role"):
            extra += " AND p.role=%s"
            xargs.append(f["role"])

        if f.get("company"):
            extra += " AND p.company=%s"
            xargs.append(f["company"])

        # 1. Overall summary
        summary = one(cur, f"""
            SELECT
                COUNT(DISTINCT s.student_id) total_students,
                COUNT(DISTINCT CASE
                    WHEN s.is_eligible=1 THEN s.student_id
                END) eligible_students,
                COUNT(DISTINCT CASE
                    WHEN p.status='PLACED' THEN s.student_id
                END) placed_students,
                ROUND(AVG(
                    CASE WHEN p.status='PLACED'
                    THEN p.package_lpa END
                ), 2) avg_package
            FROM students s
            LEFT JOIN placements p
                ON p.student_id=s.student_id
                AND p.university_id=s.university_id
                {extra}
            WHERE {w}
        """, xargs + args) or {}

        eligible = int(summary.get("eligible_students") or 0)
        placed = int(summary.get("placed_students") or 0)

        summary["placement_rate"] = (
            round(placed * 100 / eligible, 2) if eligible else 0
        )

        # 2. Department-wise analysis
        dept = all_rows(cur, f"""
            SELECT
                s.department,
                COUNT(DISTINCT s.student_id) students,
                COUNT(DISTINCT CASE
                    WHEN s.is_eligible=1 THEN s.student_id
                END) eligible,
                COUNT(DISTINCT CASE
                    WHEN p.status='PLACED' THEN s.student_id
                END) placed
            FROM students s
            LEFT JOIN placements p
                ON p.student_id=s.student_id
                AND p.university_id=s.university_id
                {extra}
            WHERE {w}
            GROUP BY s.department
            ORDER BY s.department
        """, xargs + args)


        # Calculate department-wise placement percentages
        for row in dept:
            eligible_count = int(row.get("eligible") or 0)
            placed_count = int(row.get("placed") or 0)

            row["eligible_students"] = eligible_count
            row["placed_students"] = placed_count

            row["placement_rate_percent"] = (
                round(placed_count * 100 / eligible_count, 2)
                if eligible_count else 0
            )

        # 3. Year-wise placements
        years = all_rows(cur, f"""
            SELECT
                YEAR(p.placement_date) year,
                COUNT(*) placements
            FROM placements p
            JOIN students s
                ON s.student_id=p.student_id
                AND s.university_id=p.university_id
            WHERE {w}
                AND p.status='PLACED'
                AND p.placement_date IS NOT NULL
                {extra}
            GROUP BY YEAR(p.placement_date)
            ORDER BY year
        """, args + xargs)

        # 4. Popular skills
        skill_extra = ""
        skill_args = []

        if f.get("placement_year") or f.get("role") or f.get("company"):
            skill_extra = """
                AND EXISTS (
                    SELECT 1
                    FROM placements p
                    WHERE p.student_id=s.student_id
                    AND p.university_id=s.university_id
                    AND p.status='PLACED'
            """

            if f.get("placement_year"):
                skill_extra += " AND YEAR(p.placement_date)=%s"
                skill_args.append(f["placement_year"])

            if f.get("role"):
                skill_extra += " AND p.role=%s"
                skill_args.append(f["role"])

            if f.get("company"):
                skill_extra += " AND p.company=%s"
                skill_args.append(f["company"])

            skill_extra += ")"

        skills = all_rows(cur, f"""
            SELECT
                sk.skill_name,
                COUNT(DISTINCT ss.student_id) student_count
            FROM skills sk
            JOIN student_skills ss
                ON ss.skill_id=sk.skill_id
                AND ss.university_id=%s
            JOIN students s
                ON s.student_id=ss.student_id
                AND s.university_id=ss.university_id
            WHERE {w}
                AND sk.university_id=%s
                {skill_extra}
            GROUP BY sk.skill_id, sk.skill_name
            ORDER BY student_count DESC
            LIMIT 12
        """, [tenant_id()] + args + [tenant_id()] + skill_args)

        # 5. Role-wise analysis
        roles = all_rows(cur, f"""
            SELECT
                p.role,
                COUNT(*) placement_count,
                ROUND(AVG(p.package_lpa), 2) avg_package
            FROM placements p
            JOIN students s
                ON s.student_id=p.student_id
                AND s.university_id=p.university_id
            WHERE {w}
                AND p.status='PLACED'
                {extra}
            GROUP BY p.role
            ORDER BY placement_count DESC
            LIMIT 10
        """, args + xargs)

        # 6. Company and package analysis
        packages = all_rows(cur, f"""
            SELECT
                p.company,
                p.role,
                ROUND(AVG(p.package_lpa), 2) avg_package,
                MAX(p.package_lpa) highest_package,
                COUNT(*) records
            FROM placements p
            JOIN students s
                ON s.student_id=p.student_id
                AND s.university_id=p.university_id
            WHERE {w}
                AND p.status='PLACED'
                AND p.package_lpa IS NOT NULL
                {extra}
            GROUP BY p.company, p.role
            ORDER BY avg_package DESC
        """, args + xargs)

        return {
            "summary": summary,
            "departments": dept,
            "years": years,
            "skills": skills,
            "roles": roles,
            "packages": packages
        }

    finally:
        cur.close()
        conn.close()

@app.route("/")
def home():
    return render_template("university_select.html", universities=universities())

@app.route("/select-university/<slug>")
def select_university(slug):
    conn=db(); cur=conn.cursor(dictionary=True)
    try: uni=one(cur,"SELECT university_id,name,slug FROM universities WHERE slug=%s AND is_active=1",(slug,))
    finally: cur.close(); conn.close()
    if not uni: abort(404)
    session.clear(); session["pending_university_id"]=uni["university_id"]
    session["pending_university_name"]=uni["name"]
    return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if not session.get("pending_university_id") and not session.get("university_id"):
        return redirect(url_for("home"))
    error=None
    if request.method=="POST":
        username=request.form.get("username","").strip()
        password=request.form.get("password","")
        uid=session.get("pending_university_id") or tenant_id()
        admin_u=os.getenv("PLACEMENT_USERNAME"); admin_p=os.getenv("PLACEMENT_PASSWORD")
        if admin_u and admin_p and username==admin_u and password==admin_p:
            session.clear(); session.update(logged_in=True,role="admin",username=username,university_id=uid)
            return redirect(url_for("admin_dashboard"))
        conn=db(); cur=conn.cursor(dictionary=True)
        try:
            student=one(cur,"SELECT user_id,full_name,username,password_hash FROM student_accounts WHERE username=%s AND university_id=%s",(username,uid))
            if student and check_password_hash(student["password_hash"],password):
                session.clear(); session.update(logged_in=True,role="student",user_id=student["user_id"],
                    full_name=student["full_name"],username=student["username"],university_id=uid)
                return redirect(url_for("student_dashboard"))
            error="Invalid username or password for this university."
        except Exception:
            app.logger.exception("Login failed"); error="Unable to verify account. Check database setup."
        finally: cur.close(); conn.close()
    return render_template("login.html",error=error,university=session.get("pending_university_name") or (selected_university() or {}).get("name"))

@app.route("/register",methods=["GET","POST"])
def register():
    uid=session.get("pending_university_id")
    if not uid: return redirect(url_for("home"))
    error=None
    if request.method=="POST":
        name=request.form.get("full_name","").strip(); email=request.form.get("email","").strip().lower()
        username=request.form.get("username","").strip(); password=request.form.get("password","")
        if not all([name,email,username,password]): error="Please complete every field."
        elif len(password)<8: error="Password must contain at least 8 characters."
        else:
            conn=db(); cur=conn.cursor()
            try:
                cur.execute("INSERT INTO student_accounts(university_id,full_name,email,username,password_hash) VALUES(%s,%s,%s,%s,%s)",
                    (uid,name,email,username,generate_password_hash(password)))
                conn.commit(); flash("Account created. Please log in.","success"); return redirect(url_for("login"))
            except Exception:
                conn.rollback(); error="Email or username may already be registered in this university."
            finally: cur.close(); conn.close()
    return render_template("register.html",error=error,university=session.get("pending_university_name"))

@app.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("admin_dashboard" if session["role"]=="admin" else "student_dashboard"))

@app.route("/student")
@role_required("student")
def student_dashboard():
    conn=db(); cur=conn.cursor(dictionary=True)
    try:
        me=one(cur,"SELECT * FROM students WHERE university_id=%s AND user_id=%s",(tenant_id(),session["user_id"]))
        sub=one(cur,"SELECT COUNT(*) total,SUM(verification_status='Verified') verified FROM placement_submissions WHERE university_id=%s AND user_id=%s",(tenant_id(),session["user_id"])) or {}
        skills=all_rows(cur,"SELECT sk.skill_name FROM student_skills ss JOIN skills sk ON sk.skill_id=ss.skill_id WHERE ss.university_id=%s AND ss.student_id=%s ORDER BY sk.skill_name",(tenant_id(),me["student_id"])) if me else []
        place=all_rows(cur,"SELECT company,role,package_lpa,status,placement_date FROM placements WHERE university_id=%s AND student_id=%s ORDER BY placement_date DESC",(tenant_id(),me["student_id"])) if me else []
        return render_template("student_dashboard.html",me=me,sub=sub,skills=skills,placements=place,data=analytics(),university=selected_university())
    finally: cur.close(); conn.close()

@app.route("/student/profile",methods=["GET","POST"])
@role_required("student")
def student_profile():
    conn=db(); cur=conn.cursor(dictionary=True)
    try:
        me=one(cur,"SELECT * FROM students WHERE university_id=%s AND user_id=%s",(tenant_id(),session["user_id"]))
        if request.method=="POST":
            flash("Profile changes are submitted through Submit Details for admin verification.","info")
            return redirect(url_for("student_submit"))
        return render_template("student_profile.html",me=me,university=selected_university())
    finally: cur.close(); conn.close()

@app.route("/student/skills")
@role_required("student")
def student_skills():
    conn=db(); cur=conn.cursor(dictionary=True)
    try:
        me=one(cur,"SELECT student_id,department FROM students WHERE university_id=%s AND user_id=%s",(tenant_id(),session["user_id"]))
        mine=all_rows(cur,"SELECT sk.skill_name FROM student_skills ss JOIN skills sk ON sk.skill_id=ss.skill_id WHERE ss.university_id=%s AND ss.student_id=%s ORDER BY sk.skill_name",(tenant_id(),me["student_id"])) if me else []
        popular=all_rows(cur,"SELECT sk.skill_name,COUNT(DISTINCT ss.student_id) student_count FROM skills sk JOIN student_skills ss ON ss.skill_id=sk.skill_id AND ss.university_id=%s GROUP BY sk.skill_id ORDER BY student_count DESC LIMIT 15",(tenant_id(),))
        return render_template("student_skills.html",mine=mine,popular=popular,me=me,university=selected_university())
    finally: cur.close(); conn.close()

@app.route("/student/submit",methods=["GET","POST"])
@role_required("student")
def student_submit():
    conn=db(); cur=conn.cursor(dictionary=True)
    try:
        if request.method=="POST":
            roll=request.form.get("roll_no","").strip().upper(); dept=request.form.get("department","").strip()
            year=request.form.get("graduation_year","").strip(); skills=request.form.get("skills","").strip()
            status=request.form.get("placement_status","NOT_PLACED").upper()
            company=request.form.get("company","").strip() or None; role=request.form.get("job_role","").strip() or None
            package=request.form.get("package_lpa","").strip() or None
            if not roll or not dept or not year.isdigit() or status not in {"NOT_PLACED","APPLIED","SELECTED","PLACED"}:
                flash("Check roll number, department, year and placement status.","error")
            elif status=="PLACED" and (not company or not role):
                flash("Company and job role are required for Placed status.","error")
            else:
                cur.execute("""INSERT INTO placement_submissions(university_id,user_id,roll_no,department,graduation_year,is_eligible,skills,placement_status,company,job_role,package_lpa,verification_status)
                  VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Pending')""",
                  (tenant_id(),session["user_id"],roll,dept,int(year),request.form.get("is_eligible")=="yes",skills,status,company,role,float(package) if package else None))
                conn.commit(); flash("Details submitted for verification.","success")
                return redirect(url_for("student_submit"))
        return render_template("student_submit.html",university=selected_university())
    finally: cur.close(); conn.close()

@app.route("/student/submissions")
@role_required("student")
def student_submissions():
    conn=db(); cur=conn.cursor(dictionary=True)
    try:
        rows=all_rows(cur,"SELECT submission_id,roll_no,department,graduation_year,placement_status,verification_status,admin_remarks,submitted_at,verified_at FROM placement_submissions WHERE university_id=%s AND user_id=%s ORDER BY submitted_at DESC",(tenant_id(),session["user_id"]))
        return render_template("student_submissions.html",rows=rows,university=selected_university())
    finally: cur.close(); conn.close()

@app.route("/student/placement")
@role_required("student")
def student_placement():
    conn=db(); cur=conn.cursor(dictionary=True)
    try:
        s=one(cur,"SELECT student_id FROM students WHERE university_id=%s AND user_id=%s",(tenant_id(),session["user_id"]))
        rows=all_rows(cur,"SELECT company,role,package_lpa,status,placement_date FROM placements WHERE university_id=%s AND student_id=%s ORDER BY placement_date DESC",(tenant_id(),s["student_id"])) if s else []
        return render_template("student_placement.html",rows=rows,university=selected_university())
    finally: cur.close(); conn.close()

@app.route("/student/insights")
@role_required("student")
def student_insights():
    f=filters()
    return render_template("insights.html",data=analytics(f),filters=f,university=selected_university(),departments=filter_options("department"),years=filter_options("year"))

def filter_options(kind):
    conn=db(); cur=conn.cursor(dictionary=True)
    try:
        if kind=="department": return all_rows(cur,"SELECT DISTINCT department value FROM students WHERE university_id=%s ORDER BY department",(tenant_id(),))
        return all_rows(cur,"SELECT DISTINCT graduation_year value FROM students WHERE university_id=%s ORDER BY graduation_year DESC",(tenant_id(),))
    finally: cur.close(); conn.close()

@app.route("/admin")
@role_required("admin")
def admin_dashboard():
    return render_template("admin_dashboard.html",data=analytics(),university=selected_university())


@app.route("/admin/<section>")
@role_required("admin")
def admin_section(section):
    allowed = {
        "students",
        "departments",
        "skills",
        "packages",
        "placements"
    }

    if section not in allowed:
        abort(404)

    f = filters()
    data = analytics(f)

    conn = db()
    cur = conn.cursor(dictionary=True)

    try:
        if section == "students":

            w, args = where_student(f)

            rows = all_rows(cur, f"""
                SELECT
                    s.student_id,
                    s.roll_no,
                    s.department,
                    s.graduation_year,
                    s.is_eligible,
                    sa.full_name
                FROM students s
                LEFT JOIN student_accounts sa
                    ON sa.user_id = s.user_id
                    AND sa.university_id = s.university_id
                WHERE {w}
                ORDER BY s.department, s.roll_no
                LIMIT 500
            """, args)

        elif section == "placements":

            w, args = where_student(f)

            extra = ""
            extra_args = []

            if f.get("placement_year"):
                extra += " AND YEAR(p.placement_date)=%s"
                extra_args.append(f["placement_year"])

            if f.get("role"):
                extra += " AND p.role=%s"
                extra_args.append(f["role"])

            if f.get("company"):
                extra += " AND p.company=%s"
                extra_args.append(f["company"])

            rows = all_rows(cur, f"""
                SELECT
                    s.roll_no,
                    s.department,
                    p.company,
                    p.role,
                    p.package_lpa,
                    p.status,
                    p.placement_date
                FROM placements p
                JOIN students s
                    ON s.student_id = p.student_id
                    AND s.university_id = p.university_id
                WHERE {w}
                    AND p.university_id = %s
                    {extra}
                ORDER BY p.placement_date DESC
                LIMIT 500
            """, args + [tenant_id()] + extra_args)

        elif section == "packages":

            rows = data["packages"]

        elif section == "skills":

            rows = data["skills"]

        else:

            rows = data["departments"]

        return render_template(
            "admin_section.html",
            section=section.title(),
            rows=rows,
            data=data,
            filters=f,
            university=selected_university()
        )

    finally:
        cur.close()
        conn.close()


@app.route("/admin/submissions")
@role_required("admin")
def admin_submissions():
    conn=db(); cur=conn.cursor(dictionary=True)
    try:
        rows=all_rows(cur,"""SELECT ps.*,sa.full_name,sa.email FROM placement_submissions ps
          JOIN student_accounts sa ON sa.user_id=ps.user_id AND sa.university_id=ps.university_id
          WHERE ps.university_id=%s ORDER BY (ps.verification_status='Pending') DESC,ps.submitted_at DESC""",(tenant_id(),))
        return render_template("admin_submissions.html",submissions=rows,university=selected_university())
    finally: cur.close(); conn.close()


@app.route("/admin/<section>/export")
@role_required("admin")
def export_admin_section(section):

    allowed = {
        "students", "departments", "skills",
        "packages", "placements"
    }

    if section not in allowed:
        abort(404)

    f = filters()
    rows = []

    if section in ("departments", "skills", "packages"):
        data = analytics(f)
        rows = data[section]

    else:
        conn = db()
        cur = conn.cursor(dictionary=True)

        try:
            if section == "students":
                w, args = where_student(f)

                rows = all_rows(cur, f"""
                    SELECT
                        s.student_id,
                        s.roll_no,
                        s.department,
                        s.graduation_year,
                        s.is_eligible,
                        sa.full_name
                    FROM students s
                    LEFT JOIN student_accounts sa
                        ON sa.user_id = s.user_id
                        AND sa.university_id = s.university_id
                    WHERE {w}
                    ORDER BY s.department, s.roll_no
                """, args)

            elif section == "placements":
                w, args = where_student(f)

                extra = ""
                extra_args = []

                if f.get("placement_year"):
                    extra += " AND YEAR(p.placement_date)=%s"
                    extra_args.append(f["placement_year"])

                if f.get("role"):
                    extra += " AND p.role=%s"
                    extra_args.append(f["role"])

                if f.get("company"):
                    extra += " AND p.company=%s"
                    extra_args.append(f["company"])

                rows = all_rows(cur, f"""
                    SELECT
                        s.roll_no,
                        s.department,
                        p.company,
                        p.role,
                        p.package_lpa,
                        p.status,
                        p.placement_date
                    FROM placements p
                    JOIN students s
                        ON s.student_id = p.student_id
                        AND s.university_id = p.university_id
                    WHERE {w}
                        AND p.university_id = %s
                        {extra}
                    ORDER BY p.placement_date DESC
                """, args + [tenant_id()] + extra_args)

        finally:
            cur.close()
            conn.close()

    headers = {
        "students": [
            "student_id", "roll_no", "department",
            "graduation_year", "is_eligible", "full_name"
        ],
        "departments": [
            "department", "students", "eligible", "placed",
            "eligible_students", "placed_students",
            "placement_rate_percent"
        ],
        "skills": ["skill_name", "student_count"],
        "packages": [
            "company", "role", "avg_package",
            "highest_package", "records"
        ],
        "placements": [
            "roll_no", "department", "company", "role",
            "package_lpa", "status", "placement_date"
        ]
    }

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(headers[section])

    for row in rows:
        writer.writerow([
            row.get(column, "")
            for column in headers[section]
        ])

    response = Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8"
    )

    response.headers["Content-Disposition"] = (
        f"attachment; filename={section}_records.csv"
    )

    return response


@app.route("/admin/submissions/<int:sid>/review",methods=["POST"])
@role_required("admin")
def review_submission(sid):
    decision=request.form.get("decision"); remarks=request.form.get("remarks","").strip()
    if decision not in {"Verified","Rejected"}: abort(400)
    conn=db(); cur=conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        item=one(cur,"SELECT * FROM placement_submissions WHERE submission_id=%s AND university_id=%s FOR UPDATE",(sid,tenant_id()))
        if not item or item["verification_status"]!="Pending":
            conn.rollback(); flash("Submission not found or already reviewed.","error"); return redirect(url_for("admin_submissions"))
        if decision=="Verified":
            cur.execute("""INSERT INTO students(university_id,user_id,roll_no,department,graduation_year,is_eligible)
              VALUES(%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE user_id=VALUES(user_id),department=VALUES(department),graduation_year=VALUES(graduation_year),is_eligible=VALUES(is_eligible)""",
              (tenant_id(),item["user_id"],item["roll_no"],item["department"],item["graduation_year"],item["is_eligible"]))
            student=one(cur,"SELECT student_id FROM students WHERE university_id=%s AND roll_no=%s",(tenant_id(),item["roll_no"]))
            cur.execute("DELETE FROM student_skills WHERE university_id=%s AND student_id=%s",(tenant_id(),student["student_id"]))
            for name in [x.strip() for x in (item["skills"] or "").split(",") if x.strip()]:
                cur.execute("INSERT INTO skills(university_id,skill_name) VALUES(%s,%s) ON DUPLICATE KEY UPDATE skill_name=VALUES(skill_name)",(tenant_id(),name))
                sk=one(cur,"SELECT skill_id FROM skills WHERE university_id=%s AND skill_name=%s",(tenant_id(),name))
                cur.execute("INSERT IGNORE INTO student_skills(university_id,student_id,skill_id) VALUES(%s,%s,%s)",(tenant_id(),student["student_id"],sk["skill_id"]))
            st=(item["placement_status"] or "NOT_PLACED").upper()
            if st in {"APPLIED","SELECTED","PLACED"} and item["company"] and item["job_role"]:
                cur.execute("""INSERT INTO placements(university_id,student_id,company,role,package_lpa,placement_date,status)
                  VALUES(%s,%s,%s,%s,%s,CASE WHEN %s='PLACED' THEN CURDATE() ELSE NULL END,%s)""",
                  (tenant_id(),student["student_id"],item["company"],item["job_role"],item["package_lpa"],st,st))
        cur.execute("UPDATE placement_submissions SET verification_status=%s,admin_remarks=%s,verified_at=NOW(),verified_by=%s WHERE submission_id=%s AND university_id=%s",
          (decision,remarks,session["username"],sid,tenant_id()))
        conn.commit(); flash(f"Submission {decision.lower()}.","success")
    except Exception:
        conn.rollback(); app.logger.exception("Review failed"); flash("Could not review this submission.","error")
    finally: cur.close(); conn.close()
    return redirect(url_for("admin_submissions"))

@app.route("/admin/bulk-upload",methods=["GET","POST"])
@role_required("admin")
def admin_bulk_upload():
    if request.method=="GET": return render_template("bulk_upload.html",university=selected_university())
    file=request.files.get("file")
    if not file or not file.filename.lower().endswith(".csv"):
        flash("Choose a CSV file.","error"); return redirect(url_for("admin_bulk_upload"))
    conn=db(); cur=conn.cursor()
    try:
        df=pd.read_csv(file,dtype=str).fillna("")
        needed={"roll_no","department","graduation_year","is_eligible"}
        if not needed.issubset(set(df.columns.str.strip().str.lower())): raise ValueError("CSV needs roll_no, department, graduation_year, is_eligible.")
        df.columns=df.columns.str.strip().str.lower(); inserted=0
        for _,r in df.iterrows():
            cur.execute("""INSERT IGNORE INTO students(university_id,roll_no,department,graduation_year,is_eligible)
              VALUES(%s,%s,%s,%s,%s)""",(tenant_id(),r.roll_no.strip(),r.department.strip(),int(r.graduation_year),str(r.is_eligible).lower() in {"true","1","yes"}))
            inserted+=cur.rowcount
        conn.commit(); flash(f"Imported {inserted} students into {selected_university()['name']}.","success")
    except Exception as e:
        conn.rollback(); flash(f"Upload failed: {e}","error")
    finally: cur.close(); conn.close()
    return redirect(url_for("admin_bulk_upload"))

@app.route("/api/analytics")
@login_required
def api_analytics():
    return jsonify(analytics(filters()))

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("home"))

@app.errorhandler(403)
def forbidden(e): return render_template("message.html",title="Access denied",message="This page belongs to a different account role or university."),403

if __name__=="__main__":
    app.run(debug=True)
