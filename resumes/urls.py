from django.urls import path
from . import views

app_name = "resumes"

urlpatterns = [
    # Dashboard / resume list
    path("", views.dashboard, name="dashboard"),
    # Resume creation
    path("create/", views.create_resume, name="create_resume"),
    path("<int:resume_id>/", views.resume_detail, name="resume_detail"),
    path("<int:resume_id>/edit/", views.edit_resume, name="edit_resume"),
    path("<int:resume_id>/delete/", views.delete_resume, name="delete_resume"),
    # Builder wizard
    path("<int:resume_id>/builder/", views.builder, name="builder"),
    path("<int:resume_id>/builder/personal/", views.builder_personal, name="builder_personal"),
    path("<int:resume_id>/builder/experience/", views.builder_experience, name="builder_experience"),
    path("<int:resume_id>/builder/education/", views.builder_education, name="builder_education"),
    path("<int:resume_id>/builder/skills/", views.builder_skills, name="builder_skills"),
    path("<int:resume_id>/builder/projects/", views.builder_projects, name="builder_projects"),
    path("<int:resume_id>/builder/certifications/", views.builder_certifications, name="builder_certifications"),
    path("<int:resume_id>/builder/summary/", views.builder_summary, name="builder_summary"),
    # JD targeting
    path("jd/parse/", views.parse_jd, name="parse_jd"),
    path("jd/<int:jd_id>/apply/<int:resume_id>/", views.apply_jd_to_resume, name="apply_jd_to_resume"),
    # Upload an existing resume (PDF/DOCX) and rebuild it with a new template
    path("upload/", views.upload_resume, name="upload_resume"),
    path("upload/<int:upload_id>/templates/", views.template_varieties, name="template_varieties"),
    path("upload/<int:upload_id>/preview/<str:template_style>/", views.preview_upload_template, name="preview_upload_template"),
    path("upload/<int:upload_id>/create-resume/", views.create_resume_from_upload, name="create_resume_from_upload"),
    # Preview
    path("<int:resume_id>/preview/", views. preview_resume, name="preview_resume"),
    # Export
    path("<int:resume_id>/export/docx/", views.export_docx, name="export_docx"),
    path("<int:resume_id>/export/pdf/", views.export_pdf, name="export_pdf"),
    # Versioning
    path("<int:resume_id>/version/save/", views.save_version, name="save_version"),
    path("<int:resume_id>/version/<int:version_id>/restore/", views.restore_version, name="restore_version"),
]