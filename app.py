from flask import Flask, request, redirect, url_for, render_template_string, flash
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent
DB = BASE / "kicknexa.db"
app = Flask(__name__)
app.secret_key = "CHANGE_THIS_IN_PRODUCTION"

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT,
            role TEXT NOT NULL CHECK(role IN ('athlete','organization','admin')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            organization_type TEXT NOT NULL,
            country TEXT,
            city TEXT,
            website TEXT,
            social_url TEXT,
            description TEXT,
            verification_status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            sport TEXT NOT NULL,
            opportunity_type TEXT NOT NULL,
            country TEXT,
            city TEXT,
            age_category TEXT,
            gender_category TEXT,
            description TEXT NOT NULL,
            requirements TEXT,
            application_url TEXT,
            contact_email TEXT,
            deadline TEXT,
            start_date TEXT,
            cost_amount REAL DEFAULT 0,
            currency TEXT DEFAULT 'TZS',
            verification_status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
        );
        """)
init_db()

CSS = """
body{margin:0;font-family:Inter,system-ui,Arial;background:#f7f9fc;color:#101828}
.wrap{width:min(980px,92%);margin:40px auto}.brand{font-size:26px;font-weight:900;letter-spacing:.08em}.brand span{color:#155eef}
.card{background:#fff;border:1px solid #e4e7ec;border-radius:18px;padding:26px;margin:18px 0}
h1{font-size:38px;line-height:1.05}h2{margin-top:0}label{display:block;font-weight:700;margin:14px 0 6px}
input,select,textarea{width:100%;box-sizing:border-box;padding:12px;border:1px solid #d0d5dd;border-radius:9px;font:inherit}
textarea{min-height:120px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.full{grid-column:1/-1}
button,.btn{display:inline-block;border:0;border-radius:9px;padding:12px 17px;background:#155eef;color:#fff;font-weight:800;cursor:pointer;text-decoration:none}
.muted{color:#667085}.notice{padding:12px;border-radius:10px;background:#ecfdf3;color:#027a48;margin:12px 0}
.pending{background:#fffaeb;color:#b54708}.opp{border-top:1px solid #eaecf0;padding:18px 0}.small{font-size:13px;color:#667085}
@media(max-width:700px){.grid{grid-template-columns:1fr}.full{grid-column:auto}}
"""

ORG_FORM = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Register Organization | KICKNEXA</title><style>{{css}}</style></head><body><div class="wrap">
<div class="brand">KICK<span>NEXA</span></div>
<div class="card"><h1>Register your organization</h1><p class="muted">Create an organization profile so you can publish sports opportunities. New organizations start as <b>pending</b> until verified.</p>
{% with msgs=get_flashed_messages() %}{% for m in msgs %}<div class="notice">{{m}}</div>{% endfor %}{% endwith %}
<form method="post"><div class="grid">
<div><label>Organization name<input required name="name"></label></div>
<div><label>Organization type<select name="organization_type"><option>Academy</option><option>Club</option><option>Coach</option><option>Tournament Organizer</option><option>Sports Organization</option><option>Other</option></select></label></div>
<div><label>Email<input required type="email" name="email"></label></div>
<div><label>Country<input required name="country" value="Tanzania"></label></div>
<div><label>City<input name="city"></label></div>
<div><label>Website<input type="url" name="website" placeholder="https://"></label></div>
<div class="full"><label>Social profile<input name="social_url" placeholder="https://"></label></div>
<div class="full"><label>Description<textarea name="description" placeholder="Tell athletes what your organization does"></textarea></label></div>
</div><button type="submit">Register Organization</button></form></div></div></body></html>"""

OPP_FORM = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Post Opportunity | KICKNEXA</title><style>{{css}}</style></head><body><div class="wrap">
<div class="brand">KICK<span>NEXA</span></div>
<div class="card"><h1>Post a sports opportunity</h1><p class="muted">Opportunities are created as <b>pending</b> and should be verified before public promotion.</p>
<form method="post"><div class="grid">
<div><label>Organization ID<input required type="number" name="organization_id"></label></div>
<div><label>Title<input required name="title" placeholder="U18 Football Trial"></label></div>
<div><label>Sport<input required name="sport" placeholder="Football"></label></div>
<div><label>Opportunity type<select name="opportunity_type"><option>Trial</option><option>Scholarship</option><option>Competition</option><option>Training Camp</option><option>Academy</option><option>Sponsorship</option><option>Other</option></select></label></div>
<div><label>Country<input name="country" value="Tanzania"></label></div>
<div><label>City<input name="city"></label></div>
<div><label>Age category<input name="age_category" placeholder="U18 / Open"></label></div>
<div><label>Gender/category<input name="gender_category" placeholder="Open / Female / Male"></label></div>
<div><label>Deadline<input type="date" name="deadline"></label></div>
<div><label>Start date<input type="date" name="start_date"></label></div>
<div><label>Cost (number)<input type="number" step="0.01" name="cost_amount" value="0"></label></div>
<div><label>Currency<input name="currency" value="TZS"></label></div>
<div class="full"><label>Description<textarea required name="description"></textarea></label></div>
<div class="full"><label>Requirements<textarea name="requirements"></textarea></label></div>
<div><label>Application URL<input type="url" name="application_url"></label></div>
<div><label>Contact email<input type="email" name="contact_email"></label></div>
</div><button type="submit">Submit Opportunity</button></form></div></div></body></html>"""

DASH = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KICKNEXA Opportunities</title><style>{{css}}</style></head><body><div class="wrap">
<div class="brand">KICK<span>NEXA</span></div><div class="card"><h1>Opportunity Directory</h1><p class="muted">Only verified opportunities should be promoted as verified.</p>
{% for o in opps %}<div class="opp"><h2>{{o['title']}}</h2><div><b>{{o['sport']}}</b> · {{o['opportunity_type']}} · {{o['city'] or ''}} {{o['country'] or ''}}</div><p>{{o['description']}}</p><div class="small">Organization: {{o['org_name']}} · Status: {{o['verification_status']}}{% if o['deadline'] %} · Deadline: {{o['deadline']}}{% endif %}</div></div>{% else %}<p>No opportunities yet.</p>{% endfor %}
</div></div></body></html>"""

@app.route("/")
def home():
    return redirect(url_for("opportunities"))

@app.route("/register/organization", methods=["GET","POST"])
def register_org():
    if request.method == "POST":
        f=request.form
        try:
            with db() as c:
                c.execute("INSERT INTO users(email, role) VALUES (?, 'organization')", (f["email"].strip().lower(),))
                uid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
                c.execute("""INSERT INTO organizations(user_id,name,organization_type,country,city,website,social_url,description)
                             VALUES (?,?,?,?,?,?,?,?)""",
                          (uid,f["name"],f["organization_type"],f.get("country"),f.get("city"),f.get("website"),f.get("social_url"),f.get("description")))
            flash("Organization registered. Keep the organization ID shown in your confirmation for opportunity posting.")
            return redirect(url_for("register_org"))
        except sqlite3.IntegrityError:
            flash("That email is already registered.")
    return render_template_string(ORG_FORM, css=CSS)

@app.route("/post-opportunity", methods=["GET","POST"])
def post_opportunity():
    if request.method == "POST":
        f=request.form
        with db() as c:
            org=c.execute("SELECT id FROM organizations WHERE id=?", (f["organization_id"],)).fetchone()
            if not org:
                flash("Organization ID not found.")
                return render_template_string(OPP_FORM, css=CSS)
            c.execute("""INSERT INTO opportunities
                (organization_id,title,sport,opportunity_type,country,city,age_category,gender_category,
                 description,requirements,application_url,contact_email,deadline,start_date,cost_amount,currency)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (f["organization_id"],f["title"],f["sport"],f["opportunity_type"],f.get("country"),f.get("city"),
                 f.get("age_category"),f.get("gender_category"),f["description"],f.get("requirements"),
                 f.get("application_url"),f.get("contact_email"),f.get("deadline"),f.get("start_date"),
                 float(f.get("cost_amount") or 0),f.get("currency") or "TZS"))
        flash("Opportunity submitted for verification.")
        return redirect(url_for("opportunities"))
    return render_template_string(OPP_FORM, css=CSS)

@app.route("/opportunities")
def opportunities():
    with db() as c:
        opps=c.execute("""SELECT o.*, org.name org_name FROM opportunities o
                          JOIN organizations org ON org.id=o.organization_id
                          ORDER BY o.created_at DESC""").fetchall()
    return render_template_string(DASH, css=CSS, opps=opps)

if __name__ == "__main__":
    app.run(debug=True)
