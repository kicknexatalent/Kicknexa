import os
from functools import wraps
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, redirect, url_for, render_template, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-in-production")
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required.")

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    with open("schema.sql", encoding="utf-8") as f:
        schema = f.read()
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(schema)

def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please sign in first.")
                return redirect(url_for("login", next=request.path))
            if role and session.get("role") != role:
                flash("You do not have permission to access that page.")
                return redirect(url_for("home"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def valid_url(value):
    if not value:
        return True
    p = urlparse(value)
    return p.scheme in ("http", "https") and bool(p.netloc)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health():
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "unavailable", "detail": str(e)}, 503

@app.route("/api/showcase")
def api_showcase():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, display_name, category, subcategory, city, country,
                       bio, showcase_url, verified
                FROM talent
                WHERE showcase_url IS NOT NULL AND showcase_url <> ''
                ORDER BY created_at DESC
                LIMIT 12
            """)
            return jsonify(cur.fetchall())

@app.route("/api/opportunities")
def api_opportunities():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.id, o.title, o.category, o.subcategory, o.opportunity_type,
                       o.country, o.city, o.description, o.deadline,
                       org.name AS organization_name, org.verified AS organization_verified
                FROM opportunities o
                JOIN organizations org ON org.id = o.organization_id
                WHERE o.status = 'published'
                ORDER BY o.created_at DESC
                LIMIT 12
            """)
            return jsonify(cur.fetchall())

@app.route("/register/talent", methods=["GET", "POST"])
def register_talent():
    if request.method == "POST":
        f = request.form
        email = f.get("email", "").strip().lower()
        if not email or not f.get("password") or not f.get("display_name"):
            flash("Name, email and password are required.")
            return render_template("talent_form.html")
        if f.get("showcase_url") and not valid_url(f["showcase_url"]):
            flash("Showcase URL must start with http:// or https://.")
            return render_template("talent_form.html")
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO users(email, password_hash, role)
                        VALUES (%s, %s, 'talent') RETURNING id
                    """, (email, generate_password_hash(f["password"])))
                    uid = cur.fetchone()["id"]
                    cur.execute("""
                        INSERT INTO talent
                        (user_id, display_name, category, subcategory, country, city,
                         bio, showcase_url, social_url)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        uid, f["display_name"].strip(), f["category"],
                        f.get("subcategory"), f.get("country") or "Tanzania",
                        f.get("city"), f.get("bio"), f.get("showcase_url"),
                        f.get("social_url")
                    ))
            flash("Your KICKNEXA talent profile was created.")
            return redirect(url_for("login"))
        except psycopg2.errors.UniqueViolation:
            flash("That email is already registered.")
    return render_template("talent_form.html")

@app.route("/register/organization", methods=["GET", "POST"])
def register_organization():
    if request.method == "POST":
        f = request.form
        email = f.get("email", "").strip().lower()
        if not email or not f.get("password") or not f.get("name"):
            flash("Organization name, email and password are required.")
            return render_template("org_form.html")
        if f.get("website") and not valid_url(f["website"]):
            flash("Website must start with http:// or https://.")
            return render_template("org_form.html")
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO users(email, password_hash, role)
                        VALUES (%s, %s, 'organization') RETURNING id
                    """, (email, generate_password_hash(f["password"])))
                    uid = cur.fetchone()["id"]
                    cur.execute("""
                        INSERT INTO organizations
                        (user_id, name, organization_type, country, city,
                         website, social_url, description)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        uid, f["name"].strip(), f.get("organization_type"),
                        f.get("country") or "Tanzania", f.get("city"),
                        f.get("website"), f.get("social_url"),
                        f.get("description")
                    ))
            flash("Organization registered. Your profile starts as pending verification.")
            return redirect(url_for("login"))
        except psycopg2.errors.UniqueViolation:
            flash("That email is already registered.")
    return render_template("org_form.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, email, password_hash, role FROM users WHERE email=%s",
                    (email,)
                )
                user = cur.fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["email"] = user["email"]
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Incorrect email or password.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required()
def dashboard():
    if session["role"] == "talent":
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM talent WHERE user_id=%s", (session["user_id"],))
                profile = cur.fetchone()
        return render_template("talent_dashboard.html", profile=profile)

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM organizations WHERE user_id=%s", (session["user_id"],))
            org = cur.fetchone()
            cur.execute("""
                SELECT * FROM opportunities
                WHERE organization_id=%s ORDER BY created_at DESC
            """, (org["id"],))
            opportunities = cur.fetchall()
    return render_template("org_dashboard.html", org=org, opportunities=opportunities)

@app.route("/talent")
def talent_directory():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, display_name, category, subcategory, country, city,
                       bio, showcase_url, verified
                FROM talent ORDER BY created_at DESC LIMIT 60
            """)
            talents = cur.fetchall()
    return render_template("talent_directory.html", talents=talents)

@app.route("/opportunities")
def opportunities():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.*, org.name AS organization_name,
                       org.verified AS organization_verified
                FROM opportunities o
                JOIN organizations org ON org.id=o.organization_id
                WHERE o.status='published'
                ORDER BY o.created_at DESC
            """)
            rows = cur.fetchall()
    return render_template("opportunities.html", opportunities=rows)

@app.route("/post-opportunity", methods=["GET", "POST"])
@login_required("organization")
def post_opportunity():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM organizations WHERE user_id=%s", (session["user_id"],))
            org = cur.fetchone()
    if not org:
        flash("Organization profile not found.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        f = request.form
        if f.get("application_url") and not valid_url(f["application_url"]):
            flash("Application URL must start with http:// or https://.")
            return render_template("opportunity_form.html")
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO opportunities
                    (organization_id, title, category, subcategory, opportunity_type,
                     country, city, age_category, description, requirements,
                     application_url, contact_email, deadline, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'published')
                """, (
                    org["id"], f["title"], f["category"], f.get("subcategory"),
                    f["opportunity_type"], f.get("country") or "Tanzania",
                    f.get("city"), f.get("age_category"), f["description"],
                    f.get("requirements"), f.get("application_url"),
                    f.get("contact_email"), f.get("deadline") or None
                ))
        flash("Opportunity published.")
        return redirect(url_for("dashboard"))
    return render_template("opportunity_form.html")

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
