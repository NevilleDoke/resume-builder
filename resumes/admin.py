from django.contrib import admin
from .models import (
    Resume,
    Experience,
    ExperienceBullet,
    Education,
    Skill,
    Project,
    Certification,
    JobDescription,
    ResumeVersion,
    ResumeUpload,
)


class ExperienceBulletInline(admin.TabularInline):
    model = ExperienceBullet
    extra = 3
    fields = ("text", "display_order")


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ("role", "company", "resume", "start_date", "end_date", "is_current")
    list_filter = ("is_current", "resume__target_country")
    search_fields = ("role", "company", "resume__full_name")
    inlines = [ExperienceBulletInline]


class EducationInline(admin.TabularInline):
    model = Education
    extra = 1


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 5


class ProjectInline(admin.TabularInline):
    model = Project
    extra = 2


class CertificationInline(admin.TabularInline):
    model = Certification
    extra = 2


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("title", "full_name", "email", "target_country", "target_role", "is_default", "updated_at")
    list_filter = ("target_country", "is_default", "created_at")
    search_fields = ("full_name", "email", "target_role")
    list_editable = ("is_default",)
    inlines = [EducationInline, SkillInline, ProjectInline, CertificationInline]
    fieldsets = (
        (None, {
            "fields": ("user", "title", "full_name", "email", "phone", "location", "linkedin", "github", "portfolio"),
        }),
        ("Targeting", {
            "fields": ("target_country", "target_role", "template_style", "professional_summary", "is_default"),
        }),
    )


@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "company", "raw_text")


@admin.register(ResumeVersion)
class ResumeVersionAdmin(admin.ModelAdmin):
    list_display = ("resume", "version_number", "name", "created_at")
    list_filter = ("created_at",)
    search_fields = ("resume__title", "name")


@admin.register(ResumeUpload)
class ResumeUploadAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "user", "file_type", "status", "created_at")
    list_filter = ("status", "file_type", "created_at")
    search_fields = ("original_filename", "user__username")
    readonly_fields = ("extracted_text", "parsed_data", "parse_error", "created_at")


admin.site.site_header = "Resume Builder Administration"
admin.site.site_title = "Resume Builder Admin"
admin.site.index_title = "Welcome to Resume Builder Admin"