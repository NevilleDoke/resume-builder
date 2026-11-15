# Resume Builder — Django Resume Generator

A production-grade Django-based resume builder with multi-step forms, job description targeting, country-specific templates, and **DOCX + PDF export**. Built for users around the world.

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-step Resume Builder** | Personal info, professional summary, experience, education, skills, projects, certifications |
| **Django Admin** | Full CRUD admin interface with inline editing for all resume sections |
| **Job Description Targeting** | Paste a JD → extract keywords → auto-tailor skills & summary |
| **Country-Specific Templates** | US, UK, EU/Europe, India, Canada, Australia, UAE, Singapore |
| **DOCX Export** | Professional Word document via `python-docx` |
| **PDF Export** | Print-ready PDF via `ReportLab` |
| **Versioning** | Save & restore resume snapshots for A/B testing |
| **Resume Update from File** | Upload an existing PDF/DOC/DOCX, extract its data, and rebuild it in 5 template varieties (Modern, Classic, Minimal, Creative, Executive) |
| **Tailwind CSS UI** | Production-grade responsive interface |
| **Authentication** | Per-user resume isolation (login required) |

---

## Quick Start

### 1. Activate the Virtual Environment

```cmd
venv\Scripts\activate.bat
```

### 2. Run the Development Server

```cmd
python manage.py runserver 8000
```

### 3. Access the Application

- **App:** http://localhost:8000/
- **Admin:** http://localhost:8000/admin/

**Default Admin Credentials:**
- Username: `neville`
- Password: `Admin123!`

---

## Project Structure

```
neville-personal-office-resume-builder/
├── manage.py
├── seed_data.py              # Seeds Neville Doke's resume into the DB
├── README.md
├── db.sqlite3                # SQLite database
├── resume_builder/           # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── resumes/                  # Core Django app
│   ├── models.py             # Resume, Experience, Skill, Project, Certification, JobDescription, ResumeVersion
│   ├── admin.py              # Django admin with inline forms
│   ├── views.py              # Builder, export, JD parsing, versioning views
│   ├── forms.py              # Tailwind-styled Django forms
│   ├── exports.py            # DOCX (python-docx) + PDF (ReportLab) generators
│   ├── urls.py
│   └── migrations/
├── templates/
│   ├── base.html             # Tailwind base layout
│   └── resumes/
│       ├── dashboard.html
│       ├── create_resume.html
│       ├── resume_detail.html
│       ├── edit_resume.html
│       ├── delete_confirm.html
│       ├── builder.html
│       ├── builder_step.html
│       ├── builder_experience.html
│       ├── parse_jd.html
│       ├── preview_eu.html     # EU/Europe template (matches your target format)
│       ├── preview_us.html     # US template
│       ├── preview_uk.html     # UK template
│       ├── preview_in.html     # India template
│       ├── preview_ca.html     # Canada template
│       ├── preview_au.html     # Australia template
│       ├── preview_ae.html     # UAE template
│       └── preview_sg.html     # Singapore template
├── static/                   # CSS, JS, images
├── media/                    # User uploads
├── resumes/parsing.py        # PDF/DOCX text extraction & heuristic parsing
└── venv/                     # Virtual environment
```

---

## Usage Guide

### Creating a Resume

1. Log in at `http://localhost:8000/admin/` or visit the app (auto-redirects to login).
2. On the dashboard, click **Create New Resume**.
3. Fill in personal info, target country, and target role.
4. Go to **Builder** to add experience, education, skills, projects, and certifications section by section.
5. Preview your resume in the selected country format.
6. Export as **DOCX** or **PDF**.

### Targeting a Job Description

1. From the dashboard, click **Parse Job Description**.
2. Paste the full JD text.
3. The system extracts relevant keywords (Django, FastAPI, AWS, LangChain, etc.).
4. Apply the JD to any resume to auto-add matching skills and tailor the professional summary.

### Updating an Existing Resume from a File

1. From the dashboard, click **Update Resume from File**.
2. Upload your existing resume (PDF, DOCX, or DOC, max 10 MB).
3. The system extracts the text and parses it into name, contact details, role, summary, experience, education, skills, projects, and certifications.
4. Pick one of the five template varieties — **Modern**, **Classic**, **Minimal**, **Creative**, or **Executive** — and preview your data in each layout.
5. Choose a template, give the resume a title, and click **Create Resume & Open Builder**. The new resume is saved with the extracted data and your chosen template style, ready to edit and export as DOCX/PDF.

### Country Templates

Choose a target country when creating/editing a resume. Each format adjusts conventions:

| Country | Style |
|---------|-------|
| **US** | Concise, achievement-focused, no photo/personal details |
| **UK** | Clean, skills + achievements, 2 pages typical |
| **EU / Europe** | Europass-style, detailed, personal details common |
| **India** | Detailed, academic-heavy, photo common |
| **Canada / Australia** | Similar to US/UK |
| **UAE / Singapore** | Detailed, expat-friendly |

---

## Seeding Your Existing Resume

Neville Doke's resume has been pre-seeded. To re-seed:

```cmd
python seed_data.py
```

This creates:
- **4 experiences:** KAN Infocom, Lexlegis.ai, Contexio, Green Smile
- **14 skills** across Backend, Frontend, Database, Cloud, Tools, AI/ML
- **2 projects:** Excel Manipulation Services, Google Docs to Sheets Automation
- **3 certifications:** IBM, IT Vedant, Oracle Cloud

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 5.2 |
| Database | SQLite (dev) → PostgreSQL (prod) |
| DOCX | python-docx |
| PDF | ReportLab |
| UI | Tailwind CSS (CDN) + Inter font |
| Python | 3.13 |

---

## Commands

```cmd
# Activate venv
venv\Scripts\activate.bat

# Run server
python manage.py runserver 8000

# Create superuser
python manage.py createsuperuser

# Make migrations
python manage.py makemigrations resumes

# Apply migrations
python manage.py migrate

# Seed data
python seed_data.py

# Collect static (production)
python manage.py collectstatic
```

---

## Deployment Notes

- Set `DEBUG = False` in `settings.py` for production.
- Add your domain to `ALLOWED_HOSTS`.
- Use a production WSGI server (Gunicorn/uWSGI).
- Switch from SQLite to PostgreSQL for production.
- WeasyPrint (HTML→PDF) requires GTK libraries on Linux; ReportLab is used instead for Windows compatibility.

---

## License

MIT