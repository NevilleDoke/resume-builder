"""
Resume Builder views.
Handles CRUD, multi-step builder, JD targeting, preview, and DOCX/PDF export.
"""
import json
from io import BytesIO
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone

# weasyprint imported lazily inside export_pdf to avoid GTK dependency at import time

from .models import (
    Resume, Experience, ExperienceBullet, Education, Skill,
    Project, Certification, JobDescription, ResumeVersion, ResumeUpload,
)
from .forms import (
    ResumeForm, ExperienceForm, ExperienceBulletForm,
    EducationForm, SkillForm, ProjectForm,
    CertificationForm, JobDescriptionForm, ResumeUploadForm,
)
from .exports import generate_docx, generate_pdf
from .parsing import extract_text_from_file, parse_resume_text, parse_date


def _get_user_resume(user, resume_id):
    return get_object_or_404(Resume, id=resume_id, user=user)


def _breadcrumbs(*items):
    """Build a breadcrumb list from alternating (label, url_or_None) pairs."""
    crumbs = []
    i = 0
    while i < len(items):
        label = items[i]
        url = items[i + 1] if i + 1 < len(items) else None
        crumbs.append((label, url))
        i += 2
    return crumbs


def _country_template(target_country):
    mapping = {
        "us": "resumes/preview_us.html",
        "uk": "resumes/preview_uk.html",
        "eu": "resumes/preview_eu.html",
        "in": "resumes/preview_in.html",
        "ca": "resumes/preview_ca.html",
        "au": "resumes/preview_au.html",
        "ae": "resumes/preview_ae.html",
        "sg": "resumes/preview_sg.html",
    }
    return mapping.get(target_country, "resumes/preview_us.html")


def _resume_to_dict(resume):
    """Flatten a Resume model into the same shape the parser produces, so the
    template preview can render both uploaded data and saved resumes."""
    return {
        "full_name": resume.full_name,
        "email": resume.email,
        "phone": resume.phone,
        "location": resume.location,
        "linkedin": resume.linkedin,
        "github": resume.github,
        "portfolio": resume.portfolio,
        "target_role": resume.target_role,
        "professional_summary": resume.professional_summary,
        "experiences": [
            {
                "company": e.company,
                "location": e.location,
                "role": e.role,
                "start_date": str(e.start_date) if e.start_date else "",
                "end_date": str(e.end_date) if e.end_date else "",
                "is_current": e.is_current,
                "tech_stack": e.tech_stack,
                "description": e.description,
                "bullets": [b.text for b in e.bullets.all()],
            } for e in resume.experiences.all()
        ],
        "education": [
            {
                "degree": ed.degree,
                "institution": ed.institution,
                "location": ed.location,
                "start_date": str(ed.start_date) if ed.start_date else "",
                "end_date": str(ed.end_date) if ed.end_date else "",
                "grade": ed.grade,
            } for ed in resume.education.all()
        ],
        "skills": [
            {"category": s.category, "name": s.name, "proficiency": s.proficiency}
            for s in resume.skills.all()
        ],
        "projects": [
            {
                "name": p.name,
                "description": p.description,
                "technologies": p.technologies,
                "link": p.link,
                "start_date": str(p.start_date) if p.start_date else "",
                "end_date": str(p.end_date) if p.end_date else "",
            } for p in resume.projects.all()
        ],
        "certifications": [
            {
                "name": c.name,
                "issuer": c.issuer,
                "date": str(c.date) if c.date else "",
                "link": c.link,
            } for c in resume.certifications.all()
        ],
    }


def _extract_jd_keywords(raw_text):
    common_skills = [
        "django", "fastapi", "flask", "python", "java", "spring boot",
        "react", "javascript", "typescript", "node.js", "postgresql",
        "mysql", "mongodb", "redis", "aws", "azure", "gcp", "docker",
        "kubernetes", "celery", "rest api", "graphql", "langchain",
        "rag", "openai", "llm", "vector database", "pinecone", "weaviate",
        "git", "jenkins", "ci/cd", "terraform", "linux", "sql",
        "nosql", "microservices", "event-driven", "kafka", "rabbitmq",
    ]
    text_lower = raw_text.lower()
    found = [s for s in common_skills if s in text_lower]
    seen = set()
    ordered = []
    for s in found:
        if s not in seen:
            seen.add(s)
            ordered.append(s)
    return ordered


@login_required
def dashboard(request):
    resumes = Resume.objects.filter(user=request.user).order_by("-updated_at")
    jds = JobDescription.objects.filter(user=request.user).order_by("-created_at")[:5]
    return render(request, "resumes/dashboard.html", {
        "resumes": resumes,
        "jds": jds,
        "breadcrumbs": _breadcrumbs("Dashboard", None),
    })


@login_required
def create_resume(request):
    if request.method == "POST":
        form = ResumeForm(request.POST)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            if resume.is_default:
                Resume.objects.filter(user=request.user).update(is_default=False)
            resume.save()
            messages.success(request, "Resume created successfully.")
            return redirect("resumes:builder", resume_id=resume.id)
    else:
        form = ResumeForm()
    return render(request, "resumes/create_resume.html", {
        "form": form,
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Create Resume", None,
        ),
    })


@login_required
def resume_detail(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    return render(request, "resumes/resume_detail.html", {
        "resume": resume,
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Resume", reverse("resumes:resume_detail", args=[resume.id]),
            resume.title, None,
        ),
    })


@login_required
def edit_resume(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    if request.method == "POST":
        form = ResumeForm(request.POST, instance=resume)
        if form.is_valid():
            if form.cleaned_data.get("is_default"):
                Resume.objects.filter(user=request.user).update(is_default=False)
            form.save()
            messages.success(request, "Resume updated.")
            return redirect("resumes:resume_detail", resume_id=resume.id)
    else:
        form = ResumeForm(instance=resume)
    return render(request, "resumes/edit_resume.html", {
        "form": form,
        "resume": resume,
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Resume", reverse("resumes:resume_detail", args=[resume.id]),
            "Edit Resume", None,
        ),
    })


@login_required
def delete_resume(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    if request.method == "POST":
        resume.delete()
        messages.success(request, "Resume deleted.")
        return redirect("resumes:dashboard")
    return render(request, "resumes/delete_confirm.html", {
        "resume": resume,
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Resume", reverse("resumes:resume_detail", args=[resume.id]),
            "Delete Resume", None,
        ),
    })


@login_required
def builder(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    context = {
        "resume": resume,
        "experiences": resume.experiences.all(),
        "education": resume.education.all(),
        "skills": resume.skills.all(),
        "projects": resume.projects.all(),
        "certifications": resume.certifications.all(),
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Resume", reverse("resumes:resume_detail", args=[resume.id]),
            "Builder", None,
        ),
    }
    return render(request, "resumes/builder.html", context)


@login_required
def builder_personal(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if request.method == "POST":
        form = ResumeForm(request.POST, instance=resume)
        if form.is_valid():
            if form.cleaned_data.get("is_default"):
                Resume.objects.filter(user=request.user).update(is_default=False)
            form.save()
            if is_ajax:
                return JsonResponse({
                    "status": "success",
                    "message": "Personal information saved successfully.",
                })
            messages.success(request, "Personal information updated.")
            return redirect("resumes:builder", resume_id=resume.id)
        else:
            if is_ajax:
                return JsonResponse({
                    "status": "error",
                    "message": "Please fix the errors below.",
                    "errors": form.errors,
                }, status=400)
    else:
        form = ResumeForm(instance=resume)
    return render(request, "resumes/builder_step.html", {
        "form": form,
        "resume": resume,
        "step": "Personal Information",
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Resume", reverse("resumes:resume_detail", args=[resume.id]),
            "Builder", reverse("resumes:builder", args=[resume.id]),
            "Personal Information", None,
        ),
    })


@login_required
def builder_experience(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    if request.method == "POST":
        form = ExperienceForm(request.POST)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.resume = resume
            exp.save()
            messages.success(request, "Experience added.")
            form = ExperienceForm()
    else:
        form = ExperienceForm()
    return render(request, "resumes/builder_experience.html", {
        "form": form,
        "resume": resume,
        "experiences": resume.experiences.all(),
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Resume", reverse("resumes:resume_detail", args=[resume.id]),
            "Builder", reverse("resumes:builder", args=[resume.id]),
            "Experience", None,
        ),
    })


@login_required
def builder_education(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    if request.method == "POST":
        form = EducationForm(request.POST)
        if form.is_valid():
            edu = form.save(commit=False)
            edu.resume = resume
            edu.save()
            messages.success(request, "Education added.")
            form = EducationForm()
    else:
        form = EducationForm()
    return render(request, "resumes/builder_step.html", {
        "form": form,
        "resume": resume,
        "step": "Education",
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Resume", reverse("resumes:resume_detail", args=[resume.id]),
            "Builder", reverse("resumes:builder", args=[resume.id]),
            "Education", None,
        ),
    })


@login_required
def builder_skills(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    if request.method == "POST":
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.resume = resume
            skill.save()
            messages.success(request, "Skill added.")
            form = SkillForm()
    else:
        form = SkillForm()
    return render(request, "resumes/builder_step.html", {
        "form": form,
        "resume": resume,
        "step": "Skills",
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Resume", reverse("resumes:resume_detail", args=[resume.id]),
            "Builder", reverse("resumes:builder", args=[resume.id]),
            "Skills", None,
        ),
    })


@login_required
def builder_projects(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            proj = form.save(commit=False)
            proj.resume = resume
            proj.save()
            messages.success(request, "Project added.")
            form = ProjectForm()
    else:
        form = ProjectForm()
    return render(request, "resumes/builder_step.html", {
        "form": form,
        "resume": resume,
        "step": "Projects",
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Resume", reverse("resumes:resume_detail", args=[resume.id]),
            "Builder", reverse("resumes:builder", args=[resume.id]),
            "Projects", None,
        ),
    })


@login_required
def builder_certifications(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    if request.method == "POST":
        form = CertificationForm(request.POST)
        if form.is_valid():
            cert = form.save(commit=False)
            cert.resume = resume
            cert.save()
            messages.success(request, "Certification added.")
            form = CertificationForm()
    else:
        form = CertificationForm()
    return render(request, "resumes/builder_step.html", {
        "form": form,
        "resume": resume,
        "step": "Certifications",
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Resume", reverse("resumes:resume_detail", args=[resume.id]),
            "Builder", reverse("resumes:builder", args=[resume.id]),
            "Certifications", None,
        ),
    })


@login_required
def builder_summary(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if request.method == "POST":
        form = ResumeForm(request.POST, instance=resume)
        if form.is_valid():
            if form.cleaned_data.get("is_default"):
                Resume.objects.filter(user=request.user).update(is_default=False)
            form.save()
            if is_ajax:
                return JsonResponse({
                    "status": "success",
                    "message": "Professional summary saved successfully.",
                })
            messages.success(request, "Professional summary updated.")
            return redirect("resumes:builder", resume_id=resume.id)
        else:
            if is_ajax:
                return JsonResponse({
                    "status": "error",
                    "message": "Please fix the errors below.",
                    "errors": form.errors,
                }, status=400)
    else:
        form = ResumeForm(instance=resume)
    return render(request, "resumes/builder_step.html", {
        "form": form,
        "resume": resume,
        "step": "Professional Summary",
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Resume", reverse("resumes:resume_detail", args=[resume.id]),
            "Builder", reverse("resumes:builder", args=[resume.id]),
            "Professional Summary", None,
        ),
    })


@login_required
def parse_jd(request):
    if request.method == "POST":
        form = JobDescriptionForm(request.POST)
        if form.is_valid():
            jd = form.save(commit=False)
            jd.user = request.user
            jd.extracted_keywords = _extract_jd_keywords(jd.raw_text)
            jd.save()
            messages.success(
                request,
                "JD parsed. Found " + str(len(jd.extracted_keywords)) +
                " relevant keywords: " + ", ".join(jd.extracted_keywords[:12])
            )
            return redirect("resumes:dashboard")
    else:
        form = JobDescriptionForm()
    return render(request, "resumes/parse_jd.html", {
        "form": form,
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Parse Job Description", None,
        ),
    })


@login_required
def apply_jd_to_resume(request, jd_id, resume_id):
    jd = get_object_or_404(JobDescription, id=jd_id, user=request.user)
    resume = _get_user_resume(request.user, resume_id)

    existing_skill_names = {s.name.lower() for s in resume.skills.all()}
    added = []
    for kw in jd.extracted_keywords:
        if kw.lower() not in existing_skill_names:
            Skill.objects.create(
                resume=resume,
                category="backend",
                name=kw.title(),
                proficiency="Familiar",
            )
            added.append(kw)

    if jd.extracted_keywords and not resume.professional_summary:
        keywords_str = ", ".join(jd.extracted_keywords[:8])
        resume.professional_summary = (
            "Experienced developer with expertise in " + keywords_str + ". "
            "Proven track record building scalable backend systems and AI-enabled applications."
        )
        resume.save()

    messages.success(
        request,
        "Applied " + str(len(added)) + " keywords from JD to your resume: " +
        ", ".join(added[:10])
    )
    return redirect("resumes:builder", resume_id=resume.id)


@login_required
def upload_resume(request):
    """Upload an existing resume (PDF/DOCX) to rebuild or update it."""
    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.user = request.user
            name = upload.file.name
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            upload.original_filename = name
            upload.file_type = "docx" if ext == "docx" else ("doc" if ext == "doc" else "pdf")
            upload.save()
            try:
                text = extract_text_from_file(upload.file.path, upload.file_type)
                upload.extracted_text = text
                upload.parsed_data = parse_resume_text(text)
                upload.status = "parsed"
                upload.save()
                messages.success(
                    request,
                    "File parsed successfully. Review the extracted details and pick a template below.",
                )
                return redirect("resumes:template_varieties", upload_id=upload.id)
            except Exception as exc:  # depends on file contents
                upload.status = "failed"
                upload.parse_error = str(exc)
                upload.save()
                messages.error(request, "Parsing failed: " + str(exc))
    else:
        form = ResumeUploadForm()
    return render(request, "resumes/upload_resume.html", {
        "form": form,
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Update Resume from File", None,
        ),
    })


@login_required
def template_varieties(request, upload_id):
    """Show the parsed upload data alongside every available template style."""
    upload = get_object_or_404(ResumeUpload, id=upload_id, user=request.user)
    template_styles = [
        ("modern", "Modern", "Clean centered header with an accent rule — ideal for tech roles."),
        ("classic", "Classic", "Traditional left-aligned layout with formal section rules."),
        ("minimal", "Minimal", "Plenty of whitespace and thin lines — zero distractions."),
        ("creative", "Creative", "Bold accent colours and two-column skills — stands out."),
        ("executive", "Executive", "Summary-first layout built for senior / leadership roles."),
    ]
    return render(request, "resumes/template_varieties.html", {
        "upload": upload,
        "template_styles": template_styles,
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Update Resume from File", reverse("resumes:upload_resume"),
            "Choose Template", None,
        ),
    })


@login_required
def preview_upload_template(request, upload_id, template_style):
    """Preview parsed upload data rendered in a single template style."""
    upload = get_object_or_404(ResumeUpload, id=upload_id, user=request.user)
    style_choices = dict(Resume.TEMPLATE_STYLE_CHOICES)
    if template_style not in style_choices:
        raise Http404("Unknown template style.")
    return render(request, "resumes/template_preview.html", {
        "upload": upload,
        "data": upload.parsed_data,
        "raw_text": upload.extracted_text,
        "template_style": template_style,
        "style_label": style_choices[template_style],
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Update Resume from File", reverse("resumes:upload_resume"),
            "Choose Template", reverse("resumes:template_varieties", args=[upload.id]),
            style_choices[template_style], None,
        ),
    })


@login_required
def create_resume_from_upload(request, upload_id):
    """Create a real Resume record from the parsed upload using a chosen style."""
    upload = get_object_or_404(ResumeUpload, id=upload_id, user=request.user)
    if request.method != "POST":
        return redirect("resumes:template_varieties", upload_id=upload.id)

    data = upload.parsed_data or {}
    template_style = request.POST.get("template_style", "modern")
    if template_style not in dict(Resume.TEMPLATE_STYLE_CHOICES):
        template_style = "modern"

    resume = Resume.objects.create(
        user=request.user,
        title=request.POST.get("title") or data.get("title") or "My Resume",
        full_name=data.get("full_name", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        location=data.get("location", ""),
        linkedin=data.get("linkedin", ""),
        github=data.get("github", ""),
        portfolio=data.get("portfolio", ""),
        target_role=data.get("target_role", ""),
        professional_summary=data.get("professional_summary", ""),
        template_style=template_style,
    )

    for exp in data.get("experiences", []):
        e = Experience.objects.create(
            resume=resume,
            company=exp.get("company", ""),
            location=exp.get("location", ""),
            role=exp.get("role", ""),
            start_date=parse_date(exp.get("start_date")),
            end_date=parse_date(exp.get("end_date")),
            is_current=exp.get("is_current", False),
            tech_stack=exp.get("tech_stack", ""),
            description=exp.get("description", ""),
        )
        for bullet in exp.get("bullets", []):
            if bullet.strip():
                ExperienceBullet.objects.create(experience=e, text=bullet.strip())

    for edu in data.get("education", []):
        if edu.get("institution") or edu.get("degree"):
            Education.objects.create(
                resume=resume,
                degree=edu.get("degree", ""),
                institution=edu.get("institution", ""),
                location=edu.get("location", ""),
                start_date=parse_date(edu.get("start_date")),
                end_date=parse_date(edu.get("end_date")),
                grade=edu.get("grade", ""),
            )

    for skill in data.get("skills", []):
        if skill.get("name"):
            Skill.objects.create(
                resume=resume,
                category=skill.get("category", "backend"),
                name=skill.get("name", ""),
                proficiency=skill.get("proficiency", ""),
            )

    for proj in data.get("projects", []):
        if proj.get("name"):
            Project.objects.create(
                resume=resume,
                name=proj.get("name", ""),
                description=proj.get("description", ""),
                technologies=proj.get("technologies", ""),
                link=proj.get("link", ""),
                start_date=parse_date(proj.get("start_date")),
                end_date=parse_date(proj.get("end_date")),
            )

    for cert in data.get("certifications", []):
        if cert.get("name"):
            Certification.objects.create(
                resume=resume,
                name=cert.get("name", ""),
                issuer=cert.get("issuer", ""),
                date=parse_date(cert.get("date")),
                link=cert.get("link", ""),
            )

    messages.success(
        request,
        "New resume created from your uploaded file. Review and edit it in the builder, then export.",
    )
    return redirect("resumes:builder", resume_id=resume.id)


@login_required
def preview_resume(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    style_choices = dict(Resume.TEMPLATE_STYLE_CHOICES)
    # Non-default template styles render the variety templates; everything else
    # keeps the existing country-specific HTML templates.
    if resume.template_style and resume.template_style != "modern" and resume.template_style in style_choices:
        return render(request, "resumes/template_preview.html", {
            "resume": resume,
            "data": _resume_to_dict(resume),
            "template_style": resume.template_style,
            "style_label": style_choices[resume.template_style],
            "breadcrumbs": _breadcrumbs(
                "Dashboard", reverse("resumes:dashboard"),
                "Resume", reverse("resumes:resume_detail", args=[resume.id]),
                "Preview", None,
            ),
        })
    template_name = _country_template(resume.target_country)
    return render(request, template_name, {
        "resume": resume,
        "breadcrumbs": _breadcrumbs(
            "Dashboard", reverse("resumes:dashboard"),
            "Resume", reverse("resumes:resume_detail", args=[resume.id]),
            "Preview", None,
        ),
    })


@login_required
def export_docx(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    docx_bytes = generate_docx(resume)
    filename = resume.full_name.replace(" ", "_") + "_Resume.docx"
    response = HttpResponse(
        docx_bytes,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = 'attachment; filename="' + filename + '"'
    return response


@login_required
def export_pdf(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    pdf_bytes = generate_pdf(resume)
    filename = resume.full_name.replace(" ", "_") + "_Resume.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="' + filename + '"'
    return response


@login_required
def save_version(request, resume_id):
    resume = _get_user_resume(request.user, resume_id)
    if request.method == "POST":
        data = json.loads(request.body or "{}")
        version_name = data.get("name", "Version " + timezone.now().strftime("%Y-%m-%d %H:%M"))
        last = ResumeVersion.objects.filter(resume=resume).order_by("-version_number").first()
        next_ver = (last.version_number + 1) if last else 1
        snapshot = {
            "personal": {
                "title": resume.title,
                "full_name": resume.full_name,
                "email": resume.email,
                "phone": resume.phone,
                "location": resume.location,
                "linkedin": resume.linkedin,
                "github": resume.github,
                "portfolio": resume.portfolio,
                "target_country": resume.target_country,
                "target_role": resume.target_role,
                "professional_summary": resume.professional_summary,
            },
            "experiences": [
                {
                    "company": e.company,
                    "location": e.location,
                    "role": e.role,
                    "start_date": str(e.start_date),
                    "end_date": str(e.end_date) if e.end_date else None,
                    "is_current": e.is_current,
                    "tech_stack": e.tech_stack,
                    "description": e.description,
                    "bullets": [b.text for b in e.bullets.all()],
                } for e in resume.experiences.all()
            ],
            "education": [
                {
                    "degree": ed.degree,
                    "institution": ed.institution,
                    "location": ed.location,
                    "start_date": str(ed.start_date) if ed.start_date else None,
                    "end_date": str(ed.end_date) if ed.end_date else None,
                    "grade": ed.grade,
                } for ed in resume.education.all()
            ],
            "skills": [
                {"category": s.category, "name": s.name, "proficiency": s.proficiency}
                for s in resume.skills.all()
            ],
            "projects": [
                {
                    "name": p.name,
                    "description": p.description,
                    "technologies": p.technologies,
                    "link": p.link,
                    "start_date": str(p.start_date) if p.start_date else None,
                    "end_date": str(p.end_date) if p.end_date else None,
                } for p in resume.projects.all()
            ],
            "certifications": [
                {
                    "name": c.name,
                    "issuer": c.issuer,
                    "date": str(c.date) if c.date else None,
                    "link": c.link,
                } for c in resume.certifications.all()
            ],
        }
        ResumeVersion.objects.create(
            resume=resume,
            version_number=next_ver,
            name=version_name,
            snapshot=snapshot,
        )
        return HttpResponse(json.dumps({"status": "ok", "version": next_ver}), content_type="application/json")
    return HttpResponse(status=405)


@login_required
def restore_version(request, resume_id, version_id):
    resume = _get_user_resume(request.user, resume_id)
    version = get_object_or_404(ResumeVersion, id=version_id, resume=resume)
    snap = version.snapshot

    p = snap.get("personal", {})
    resume.title = p.get("title", resume.title)
    resume.full_name = p.get("full_name", resume.full_name)
    resume.email = p.get("email", resume.email)
    resume.phone = p.get("phone", resume.phone)
    resume.location = p.get("location", resume.location)
    resume.linkedin = p.get("linkedin", resume.linkedin)
    resume.github = p.get("github", resume.github)
    resume.portfolio = p.get("portfolio", resume.portfolio)
    resume.target_country = p.get("target_country", resume.target_country)
    resume.target_role = p.get("target_role", resume.target_role)
    resume.professional_summary = p.get("professional_summary", resume.professional_summary)
    resume.save()

    resume.experiences.all().delete()
    for exp in snap.get("experiences", []):
        e = Experience.objects.create(
            resume=resume,
            company=exp.get("company", ""),
            location=exp.get("location", ""),
            role=exp.get("role", ""),
            start_date=exp.get("start_date") or date.today(),
            end_date=exp.get("end_date") or None,
            is_current=exp.get("is_current", False),
            tech_stack=exp.get("tech_stack", ""),
            description=exp.get("description", ""),
        )
        for bullet in exp.get("bullets", []):
            ExperienceBullet.objects.create(experience=e, text=bullet)

    resume.education.all().delete()
    for ed in snap.get("education", []):
        Education.objects.create(
            resume=resume,
            degree=ed.get("degree", ""),
            institution=ed.get("institution", ""),
            location=ed.get("location", ""),
            start_date=ed.get("start_date") or None,
            end_date=ed.get("end_date") or None,
            grade=ed.get("grade", ""),
        )

    resume.skills.all().delete()
    for s in snap.get("skills", []):
        Skill.objects.create(
            resume=resume,
            category=s.get("category", "backend"),
            name=s.get("name", ""),
            proficiency=s.get("proficiency", ""),
        )

    resume.projects.all().delete()
    for pj in snap.get("projects", []):
        Project.objects.create(
            resume=resume,
            name=pj.get("name", ""),
            description=pj.get("description", ""),
            technologies=pj.get("technologies", ""),
            link=pj.get("link", ""),
            start_date=pj.get("start_date") or None,
            end_date=pj.get("end_date") or None,
        )

    resume.certifications.all().delete()
    for c in snap.get("certifications", []):
        Certification.objects.create(
            resume=resume,
            name=c.get("name", ""),
            issuer=c.get("issuer", ""),
            date=c.get("date") or None,
            link=c.get("link", ""),
        )

    messages.success(request, "Restored '" + version.name + "' successfully.")
    return redirect("resumes:builder", resume_id=resume.id)
