# Copilot Context — StrokeCare (COM7033 Secure Software Development)

Author: Vaishali (MSc DS&AI)
Goal: Build a secure dual-database Flask app with **RBAC** (admin, doctor, healthcare, patient), clear **SSDLC** artifacts, and a modern **violet** UI.

Tech: Flask • Jinja2 • WTForms • Flask-Login • SQLAlchemy (SQLite for auth) • PyMongo (MongoDB for patients) • Vanilla JS • CSS • Bootstrap

---

## 0) Non-negotiables (what to always assume)
- All forms use **Flask-WTF + CSRF**.
- All responses set **security headers** (CSP, XFO, XCTO, Referrer-Policy, Permissions-Policy).
- **RBAC** guards on server (never rely on hide-in-UI).
- **Audit logs** for sensitive actions.
- **Error pages** (403/404) — never show stack traces to end users.
- **Input is hostile** → validate + coerce types + escape outputs.
- **Principle of least privilege** everywhere.

---

## 1) Project structure (Copilot, keep to this)
```
app/
  __init__.py           # create_app(), security headers, blueprint register
  config.py             # Config classes + load_config()
  extensions.py         # db (SQLAlchemy), login_manager, csrf, limiter (optional)
  rbac.py               # permission helpers
  models.py             # SQLite models: User, Session, AuditLog
  forms.py              # WTForms: Login/Register/Patient/Reset
  routes/
    __init__.py
    main.py             # role-based home redirect
    auth.py             # login/register/forgot/reset/logout
    admin.py            # admin-only: users, audit, settings
    patients.py         # list/detail/create/update/delete/predict
    privacy.py          # policy page
  utils/
    audit.py            # audit(action, resource, id, details)
    risk.py             # compute_risk()
    mongo.py            # get_patient_coll(), helpers
  templates/
    base.html
    _partials/navbar.html
    errors/{403.html,404.html}
    auth/{login.html,register.html,forgot.html,reset.html}
    admin/{index.html,users.html,audit.html,settings.html}
    dashboard/{clinical.html,care.html}
    patients/{index.html,detail.html}
    my/{index.html,predictions.html}
  static/
    css/theme.css
    js/main.js
instance/
  stroke.db             # created at runtime (gitignored)
scripts/
  seed_sqlite.py
  seed_mongo.py
tests/
  test_auth.py test_rbac.py test_patients.py test_risk.py
.vscode/settings.json   # analysis config
.env.example            # see below
```

---

## 2) Environment & run instructions

**`.env.example`**
```
FLASK_ENV=development
SECRET_KEY=change-this
SQLALCHEMY_DATABASE_URI=sqlite:///stroke.db
MONGO_URI=mongodb://localhost:27017/strokecare
SECURITY_SESSION_MINUTES=60
REMEMBER_COOKIE_DAYS=7
WTF_CSRF_TIME_LIMIT=86400
```

**Run**
```
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/seed_sqlite.py
python scripts/seed_mongo.py
flask --app run.py run  # or python run.py
```

**Seed accounts (for tests & demos)**
- admin: admin@sc.app / Passw0rd!
- doctor: dr@sc.app / Passw0rd!
- healthcare: nurse@sc.app / Passw0rd!
- patient: pat@sc.app / Passw0rd!

---

## 3) Security model (OWASP-aligned)

### 3.1 Authentication & Sessions
- Passwords → `generate_password_hash` / `check_password_hash`.
- Session lifetime → `PERMANENT_SESSION_LIFETIME` using `SECURITY_SESSION_MINUTES`.
- `login_user(user, remember=form.remember.data)`; implement `/logout` and clear session.
- Brute force: Optional `Flask-Limiter` (`"5/minute; 20/hour"` for `/auth/login`).

### 3.2 Authorization (RBAC)
Roles: `admin`, `doctor`, `healthcare`, `patient`.

Permissions:
```
patient.view_all, patient.view_own, patient.create, patient.edit, patient.delete,
ml.run, ml.view, user.manage, audit.view, system.settings
```

Matrix:

| Feature/Perm             | admin | doctor | healthcare | patient |
|--------------------------|:-----:|:------:|:----------:|:------:|
| View all patients        |  ✓    |   ✓    |     ✓      |   ✗    |
| View own record          |  ✓    |   ✓    |     ✓      |   ✓    |
| Add patient              |  ✓    |   ✓    |     ✓      |   ✗    |
| Edit patient             |  ✓    |   ✓    |     ✓      |   ✗    |
| Delete patient           |  ✓    |   ✗    |     ✗      |   ✗    |
| Run ML prediction        |  ✓    |   ✓    |     ✓      |   ✗    |
| View ML predictions      |  ✓    |   ✓    |     ✓      |   ✓(own)|
| Manage users             |  ✓    |   ✗    |     ✗      |   ✗    |
| View audit logs          |  ✓    |   ✗    |     ✗      |   ✗    |
| System settings          |  ✓    |   ✗    |     ✗      |   ✗    |

Helpers (in `rbac.py`):
```python
def require_permissions(*perms): ...
def role_is(*roles): ...
```

### 3.3 CSRF & Input Validation
- Every form subclass of `FlaskForm`; render `{{ form.csrf_token }}`.
- WTForms validators: `DataRequired`, `Email`, `Length`, `NumberRange`, `EqualTo`.
- Coerce numerics: `DecimalField` with `places`; `IntegerField` with bounds.

### 3.4 Output Encoding
- Jinja escapes by default; never mark user strings `|safe`.
- Avoid concatenating HTML in Python.

### 3.5 Security Headers (in `@app.after_request`)
- **CSP**: self + `cdn.jsdelivr.net` for CSS/JS; `fonts.googleapis.com` & `fonts.gstatic.com`.
- **X-Content-Type-Options: nosniff**
- **X-Frame-Options: DENY**
- **Referrer-Policy: no-referrer**
- **Permissions-Policy:** disable geo, mic, camera.

### 3.6 Secrets & Dependencies
- Secrets live in `.env` (never commit).
- Pin versions in `requirements.txt`.
- Run `pip-audit` (optional CI step) and keep a minimal surface area.

### 3.7 Logging & Auditing
- `utils/audit.py`:
  ```python
  def audit(action, resource_type=None, resource_id=None, details=None): ...
  ```
- Log: `login`, `logout`, `patient.create/update/delete/predict`, `user.create/update/delete`, `settings.update`.
- Error handler logs exception (server), shows friendly error page (client).

### 3.8 Data Protection
- SQLite holds **auth only** (least privilege), MongoDB holds **clinical** data.
- Optional merit: field-level encryption for `avg_glucose_level` + `bmi` before Mongo insert.
- Soft delete in Mongo via `system_metadata.is_active=false`.

### 3.9 Rate Limiting (bonus)
- `Limiter` on login and heavy endpoints (predict).

---

## 4) Databases

### 4.1 SQLite (SQLAlchemy)
```python
class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password_hash = db.Column(db.String(255), nullable=False)
  role = db.Column(db.String(32), default="patient", nullable=False)
  is_active = db.Column(db.Boolean, default=True)
  created_at = db.Column(db.DateTime, default=datetime.utcnow)
  last_login = db.Column(db.DateTime)

class Session(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
  session_token = db.Column(db.String(64), unique=True, index=True, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.utcnow)
  expires_at = db.Column(db.DateTime, nullable=False)
  ip_address = db.Column(db.String(45))

class AuditLog(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
  action = db.Column(db.String(64), nullable=False)
  resource_type = db.Column(db.String(64))
  resource_id = db.Column(db.String(64))
  details = db.Column(db.Text)
  timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
```

### 4.2 MongoDB (PyMongo)
Patients collection document:
```json
{
  "_id": "ObjectId",
  "orig_id": 123,
  "demographics": { "gender":"Female","age":67,"ever_married":"Yes","work_type":"Private","residence_type":"Urban" },
  "medical_history": { "hypertension":1,"heart_disease":0,"avg_glucose_level":210.1,"bmi":31.2,"smoking_status":"formerly smoked","stroke":0 },
  "risk_assessment": { "score":6,"level":"High","factors":["age≥55","hypertension","glucose>200","bmi≥30","smoking history"],"calculated_at":"2025-01-01T12:33:00Z" },
  "system_metadata": { "created_by":1,"created_at":"2025-01-01T12:00:00Z","last_modified_by":1,"last_modified_at":"2025-01-01T12:33:00Z","is_active":true }
}
```

`utils/mongo.py` exposes: `get_patient_coll()`, `find_by_id()`, `list_paginated(query, page, size)`, `insert_patient(doc)`, `update_patient(id, update)`, `soft_delete(id)`.

---

## 5) Routes & pages (role-aware)

### Entry & redirects
- `/` → by role:
  - admin → `/admin`
  - doctor → `/dashboard/clinical`
  - healthcare → `/dashboard/care`
  - patient → `/me`

### Auth
- `GET/POST /auth/login` — LoginForm
- `GET/POST /auth/register` — RegisterForm (only admin in prod; dev open)
- `GET/POST /auth/forgot`, `GET/POST /auth/reset/<token>`
- `GET /logout` — logs out + audit

### Admin
- `/admin` (KPIs: users, active sessions, patients total), last 10 audit entries, quick links to Users/Audit/Settings.
- `/admin/users` (CRUD, restrict deleting last admin)
- `/admin/audit` (filter by action/user/date)
- `/admin/settings` (env read-only; allow toggling features flags saved to SQLite)

### Patients (doctor/healthcare/admin; patient view own only)
- `GET /patients?page=&q=` — list with search, pagination
- `GET /patients/<id>` — detail with risk chip
- `POST /patients` — create
- `POST /patients/<id>` — update
- `POST /patients/<id>/delete` — admin only
- `POST /patients/<id>/predict` — compute & persist risk (doctor/healthcare/admin)

### Patient self area
- `/me` — profile + latest risk
- `/me/predictions` — view-only list of their assessments

### Privacy & errors
- `/privacy` → policy
- 403/404 → pretty templates

---

## 6) Forms (WTForms)
```python
class LoginForm(FlaskForm):
  email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=120)])
  password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
  remember = BooleanField("Remember me")
  submit = SubmitField("Sign in")

class RegisterForm(FlaskForm):
  email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=120)])
  role = SelectField("Role", choices=[("doctor","Doctor"),("healthcare","Healthcare"),("patient","Patient")])
  password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
  confirm = PasswordField("Confirm password", validators=[EqualTo("password")])
  submit = SubmitField("Create account")

class PatientForm(FlaskForm):
  gender = SelectField("Gender", choices=[("Male","Male"),("Female","Female"),("Other","Other")])
  age = IntegerField("Age", validators=[NumberRange(min=0, max=120)])
  ever_married = SelectField("Married", choices=[("Yes","Yes"),("No","No")])
  work_type = SelectField("Work", choices=[("children","Children"),("Govt_job","Govt_job"),("Never_worked","Never_worked"),("Private","Private"),("Self-employed","Self-employed")])
  residence_type = SelectField("Residence", choices=[("Urban","Urban"),("Rural","Rural")])
  hypertension = SelectField("Hypertension", choices=[("0","No"),("1","Yes")])
  heart_disease = SelectField("Heart disease", choices=[("0","No"),("1","Yes")])
  avg_glucose_level = DecimalField("Avg glucose", places=2)
  bmi = DecimalField("BMI", places=1)
  smoking_status = SelectField("Smoking", choices=[("formerly smoked","Formerly"),("never smoked","Never"),("smokes","Smokes"),("Unknown","Unknown")])
  submit = SubmitField("Save")
```

---

## 7) Risk scoring (simple, deterministic)
```python
def compute_risk(mh, demo):
  score, factors = 0, []
  if demo.get("age",0) >= 55: score+=3; factors.append("age≥55")
  if str(mh.get("hypertension")) in ("1","True","true"): score+=2; factors.append("hypertension")
  if str(mh.get("heart_disease")) in ("1","True","true"): score+=2; factors.append("heart disease")
  if float(mh.get("avg_glucose_level",0)) > 200: score+=2; factors.append("glucose>200")
  if float(mh.get("bmi",0)) >= 30: score+=1; factors.append("bmi≥30")
  if mh.get("smoking_status") in ("smokes","formerly smoked"): score+=1; factors.append("smoking history")
  level = "Low" if score<=2 else ("Medium" if score<=4 else "High")
  return score, level, factors
```

---

## 8) UI system — Violet theme

**Design tokens (`static/css/theme.css`)**
```css
:root{
  --violet-50:#f5f3ff; --violet-100:#ede9fe; --violet-200:#ddd6fe;
  --violet-300:#c4b5fd; --violet-400:#a78bfa; --violet-500:#8b5cf6;
  --violet-600:#7c3aed; --violet-700:#6d28d9; --violet-800:#5b21b6; --violet-900:#4c1d95;

  --bg:#0f0f13; --card:rgba(255,255,255,.06); --border:rgba(255,255,255,.12);
  --text:#eaeaf2; --muted:#cfd1dd; --danger:#ef4444; --success:#22c55e;
}
body{background:var(--bg);color:var(--text);font-family:Inter,system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
a,.link{color:var(--violet-300)} a:hover{color:var(--violet-100)}
.navbar{backdrop-filter:saturate(120%) blur(8px);-webkit-backdrop-filter:saturate(120%) blur(8px);border-bottom:1px solid var(--border)}
.card{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:1rem;backdrop-filter:saturate(120%) blur(8px);-webkit-backdrop-filter:saturate(120%) blur(8px)}
.input,.select,textarea{background:rgba(255,255,255,.06);border:1px solid var(--border);color:var(--text);border-radius:10px;padding:.6rem .8rem}
.btn{display:inline-flex;gap:.5rem;align-items:center;border-radius:12px;padding:.65rem 1rem;border:0;cursor:pointer}
.btn-violet{background:var(--violet-600);color:#fff}.btn-violet:hover{background:var(--violet-500)}
.btn-outline{background:transparent;border:1px solid var(--border)}
.alert{border:1px solid var(--border);border-radius:12px;padding:.75rem 1rem;margin:.5rem 0}
.alert-success{background:rgba(34,197,94,.12)} .alert-danger{background:rgba(239,68,68,.12)}
.badge{border-radius:999px;padding:.25rem .6rem;border:1px solid var(--border)}
.badge-low{background:rgba(34,197,94,.12)} .badge-medium{background:rgba(234,179,8,.15)} .badge-high{background:rgba(239,68,68,.12)}
.table{width:100%;border-collapse:separate;border-spacing:0 .5rem}
.table th{color:var(--muted);font-weight:600;text-align:left}
.table tr{background:var(--card);border:1px solid var(--border)}
.table td,.table th{padding:.75rem 1rem}
```

**Role dashboards (wire intent)**
- **Admin**: metrics cards (users, active sessions, patients total), last 10 audit entries, quick links to Users/Audit/Settings.
- **Doctor**: “Today’s patients”, quick “Run prediction” button per row (POST → JSON flash), shortcuts to Patient list.
- **Healthcare**: Patient care queue (view/edit), no delete; charts (risk levels).
- **Patient**: personal profile card + latest risk chip + read-only predictions list.

---

## 9) SSDLC to implement (and show in report)

### 9.1 Planning
- Use the Lucidchart set: **System Architecture**, **Data Flow**, **Security Architecture**, **Database Schema**, **RBAC Table**, **User Journey**, **SSDLC Workflow**, **Risk Assessment Flow**.
- Requirements: authentication, RBAC, patient CRUD, risk compute, audit, dashboards, privacy page.

### 9.2 Design
- Threat model (STRIDE) highlights:
  - **S**poofing: credential attacks → rate limit + strong hashing + lockouts (optional).
  - **T**ampering: CSRF, parameter tampering → CSRF + server side validation.
  - **R**epudiation: add **AuditLog**.
  - **I**nformation disclosure: strict CSP, least privilege DB split, no stack traces.
  - **D**enial of service: limiter on heavy endpoints.
  - **E**levation of privilege: enforce RBAC on server + deny by default.

### 9.3 Implementation
- Follow this file. Keep code typed (`-> None`, `-> dict`) where useful.
- Use helpers (`audit`, `require_permissions`, `compute_risk`) to standardize patterns.
- Avoid inline SQL; always parameterized ORM.

### 9.4 Verification & Testing
- **Unit tests**
  - `compute_risk()` boundaries, WTForms validators.
  - RBAC: endpoint returns 403 for insufficient role.
- **Integration tests**
  - Login flow happy/sad paths.
  - Create patient → predict → verify persisted risk in Mongo.
  - Patient cannot access others’ records.
- **Security checks**
  - CSRF token required (assert 400/403 when absent).
  - Security headers present on a sample page.
- **Lighthouse (optional)**: accessibility & performance passes.

### 9.5 Deployment & Maintenance
- `.env` via secrets store; rotate `SECRET_KEY` on schedule.
- DB backups: SQLite file snapshot; Mongo dump for `strokecare`.
- Logs rotation (if deployed).
- **Update policy**: monthly dependency review; `pip-upgrade` and test.

### 9.6 Documentation
- This context file (design & security).
- Short **README** with run steps, role accounts, and screenshots.
- Comment blocks above sensitive helpers explaining security rationale.

---

## 10) Coding conventions

- Commit style:
  `feat(auth):`, `feat(patients):`, `feat(ml):`, `sec(headers):`, `ui(theme):`, `refactor:`, `test:`
  In body, reference diagram: “Aligned with **Data Flow Diagram v3**”.

- Error handling: log server-side, flash friendly message, return 4xx/5xx page.

- Pagination default: 10 per page (`?page=1&size=10`).

---

## 11) Concrete patterns for Copilot to mimic

### 11.1 After-request headers (CSP etc.)
```python
@app.after_request
def _secure_headers(resp):
  resp.headers.setdefault("Content-Security-Policy",
    "default-src 'self'; "
    "script-src 'self' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'")
  resp.headers.setdefault("Referrer-Policy", "no-referrer")
  resp.headers.setdefault("X-Content-Type-Options", "nosniff")
  resp.headers.setdefault("X-Frame-Options", "DENY")
  resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
  return resp
```

### 11.2 RBAC decorator usage
```python
@bp.get("/patients")
@login_required
@require_permissions("patient.view_all")
def patients_index(): ...
```

### 11.3 Risk compute call in controller
```python
score, level, factors = compute_risk(doc["medical_history"], doc["demographics"])
coll.update_one({"_id": oid}, {"$set": {"risk_assessment": {"score":score,"level":level,"factors":factors,"calculated_at": datetime.utcnow()}}})
audit("patient.predict", "patient", str(oid), f"level={level}")
```

### 11.4 Flash messages + alerts
```jinja
{% with msgs = get_flashed_messages(with_categories=true) %}
  {% for cat, msg in msgs %}
    <div class="alert {{ 'alert-success' if cat=='success' else 'alert-danger' }}">{{ msg }}</div>
  {% endfor %}
{% endwith %}
```

---

## 12) Accessibility & UX
- Color contrast: text on violet ≥ WCAG AA; use `--violet-600` for buttons, `--violet-500` hover.
- Keyboard reachable forms and buttons; `:focus-visible` outlines.
- aria-labels on icon-only buttons.

---

## 13) Performance
- Use CDN for fonts/css (whitelisted in CSP).
- Server-side pagination; avoid returning large JSON.
- Cache static assets with far-future headers (Flask static does ETags by default).

---

## 14) What to generate next (Copilot tasks)
1. `rbac.py` with `require_permissions` + `role_is`.
2. `utils/audit.py` and wire to SQLite.
3. `utils/mongo.py` with typed helpers.
4. `routes/auth.py` (login/register/forgot/reset/logout), with CSRF and audit.
5. `routes/main.py` role redirect.
6. `routes/admin.py`, `routes/patients.py`, `routes/privacy.py`.
7. `templates/base.html` + navbar + violet theme tokens.
8. Screens per role as listed in §5.
9. Unit & integration tests in `tests/`.

> Always: protect routes with `@login_required` + RBAC. Validate inputs. Flash friendly errors. Audit sensitive operations.
```

---

## Also add this VS Code file

**`.vscode/settings.json`**
```json
{
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.extraPaths": ["."],
  "editor.formatOnSave": true,
  "files.exclude": { "**/__pycache__": true }
}
```
