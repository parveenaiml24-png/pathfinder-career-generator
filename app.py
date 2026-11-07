import csv
import io
import re
import secrets
from functools import wraps

from flask import (
    Flask, Response, flash, g, redirect, render_template, request, send_file,
    session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from database.db import close_db, get_db, init_db, profile_to_dict
from services.ai_service import generate_career_content
from services.career_service import (
    get_progress, latest_generation, save_generation, save_progress,
)
from services.pdf_service import career_profile_pdf

app = Flask(__name__)
app.config.from_object(Config)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
app.teardown_appcontext(close_db)


@app.before_request
def prepare_request():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    if session.get("user_id"):
        with get_db() as db:
            g.user = db.execute(
                "SELECT id, name, email FROM users WHERE id = ?",
                (session["user_id"],),
            ).fetchone()
        if not g.user:
            session.clear()
    else:
        g.user = None


@app.before_request
def protect_post_requests():
    if request.method == "POST":
        supplied = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        if not supplied or not secrets.compare_digest(supplied, expected):
            return "Your session token expired. Please reload the page and try again.", 400


@app.context_processor
def template_context():
    return {"csrf_token": session.get("csrf_token", "")}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.user:
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_career_data():
    payload, generated_at = latest_generation(g.user["id"])
    return payload, generated_at


@app.route("/")
def index():
    if g.user:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(name) < 2 or len(name) > 80:
            flash("Please enter a name between 2 and 80 characters.", "error")
        elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Enter a valid email address.", "error")
        elif len(password) < 8:
            flash("Use a password with at least 8 characters.", "error")
        else:
            try:
                with get_db() as db:
                    cursor = db.execute(
                        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                        (name, email, generate_password_hash(password)),
                    )
                    db.execute("INSERT INTO profiles (user_id) VALUES (?)", (cursor.lastrowid,))
                session.clear()
                session["user_id"] = cursor.lastrowid
                session["csrf_token"] = secrets.token_urlsafe(32)
                flash("Your account is ready. Complete your profile to get started.", "success")
                return redirect(url_for("profile"))
            except Exception as error:
                if "UNIQUE constraint failed" not in str(error):
                    raise
                flash("An account with that email already exists.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Email or password is incorrect.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["csrf_token"] = secrets.token_urlsafe(32)
            return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    payload, generated_at = current_career_data()
    progress = get_progress(g.user["id"])
    roadmap = payload.get("roadmap", []) if payload else []
    completed = sum(progress.get(item.get("focus", ""), False) for item in roadmap)
    return render_template(
        "dashboard.html", payload=payload, generated_at=generated_at,
        profile=_profile(), completed=completed, roadmap_count=len(roadmap),
    )


def _profile():
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM profiles WHERE user_id = ?", (g.user["id"],)
        ).fetchone()
    return profile_to_dict(row)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        fields = {
            "degree": 100, "branch": 100, "semester": 40, "interests": 1000,
            "technical_skills": 1000, "languages": 500, "career_goals": 1000,
            "domain": 100, "resume_text": 5000,
        }
        data = {field: request.form.get(field, "").strip()[:limit] for field, limit in fields.items()}
        data["skill_level"] = request.form.get("skill_level", "Beginner")
        if data["skill_level"] not in {"Beginner", "Intermediate", "Advanced"}:
            flash("Select a valid skill level.", "error")
        elif not data["degree"] or not data["branch"] or not data["domain"] or not data["career_goals"]:
            flash("Degree, branch, career goal, and preferred domain are required.", "error")
        else:
            with get_db() as db:
                db.execute(
                    """UPDATE profiles SET degree = ?, branch = ?, semester = ?, interests = ?,
                    technical_skills = ?, languages = ?, career_goals = ?, domain = ?,
                    skill_level = ?, resume_text = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?""",
                    (
                        data["degree"], data["branch"], data["semester"], data["interests"],
                        data["technical_skills"], data["languages"], data["career_goals"],
                        data["domain"], data["skill_level"], data["resume_text"], g.user["id"],
                    ),
                )
            flash("Profile saved. Generate your personalized career plan when ready.", "success")
            return redirect(url_for("dashboard"))
    return render_template("profile.html", profile=_profile())


@app.post("/generate")
@login_required
def generate():
    student_profile = _profile()
    missing = [key for key in ("degree", "branch", "domain", "career_goals") if not student_profile.get(key)]
    if missing:
        flash("Complete your degree, branch, career goal, and preferred domain first.", "error")
        return redirect(url_for("profile"))
    student_profile["name"] = g.user["name"]
    try:
        payload = generate_career_content(
            student_profile, app.config["GEMINI_API_KEY"], app.config["GEMINI_MODEL"]
        )
    except (ValueError, RuntimeError) as error:
        app.logger.exception("Career content generation failed")
        flash(f"Could not generate the profile: {error}", "error")
        return redirect(url_for("dashboard"))
    except Exception:
        app.logger.exception("Career content provider request failed")
        flash("AI generation failed. Check your API configuration or try again later.", "error")
        return redirect(url_for("dashboard"))
    save_generation(g.user["id"], payload)
    flash(
        "Career plan generated using " + ("Gemini AI." if payload.get("mode") == "gemini" else "demo mode."),
        "success",
    )
    return redirect(url_for("career_profile"))


@app.route("/career")
@login_required
def career_profile():
    payload, generated_at = current_career_data()
    return render_template("career_profile.html", payload=payload, generated_at=generated_at)


@app.route("/skill-gap")
@login_required
def skill_gap():
    payload, generated_at = current_career_data()
    return render_template("skill_gap.html", payload=payload, generated_at=generated_at)


@app.route("/learning")
@login_required
def learning_roadmap():
    payload, generated_at = current_career_data()
    return render_template(
        "learning_roadmap.html", payload=payload, generated_at=generated_at,
        progress=get_progress(g.user["id"]),
    )


@app.post("/progress")
@login_required
def update_progress():
    item = request.form.get("item", "").strip()[:200]
    if not item:
        flash("Could not update progress: roadmap item is missing.", "error")
        return redirect(url_for("learning_roadmap"))
    save_progress(g.user["id"], {item: request.form.get("completed") == "1"})
    return redirect(url_for("learning_roadmap"))


@app.route("/interview")
@login_required
def interview_prep():
    payload, generated_at = current_career_data()
    return render_template("interview_prep.html", payload=payload, generated_at=generated_at)


@app.route("/download/profile.pdf")
@login_required
def download_pdf():
    payload, _ = current_career_data()
    if not payload:
        flash("Generate a career profile before downloading.", "info")
        return redirect(url_for("dashboard"))
    return send_file(
        career_profile_pdf(payload, g.user["name"]),
        mimetype="application/pdf", as_attachment=True, download_name="career-profile.pdf",
    )


@app.route("/download/skills.csv")
@login_required
def download_skills():
    payload, _ = current_career_data()
    if not payload:
        flash("Generate a career profile before exporting skill analysis.", "info")
        return redirect(url_for("dashboard"))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Skill", "Status", "Proficiency"])
    analysis = payload.get("skill_analysis", {})
    levels = {item["skill"]: item.get("level", "") for item in analysis.get("proficiency", [])}
    for skill in analysis.get("required", []):
        status = "Current" if skill in analysis.get("current", []) else "To develop"
        writer.writerow([skill, status, levels.get(skill, "")])
    return Response(
        output.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=skill-gap-report.csv"},
    )


@app.errorhandler(413)
def request_too_large(_error):
    flash("The submitted data is too large. Shorten the resume text and try again.", "error")
    return redirect(url_for("profile"))


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True)
