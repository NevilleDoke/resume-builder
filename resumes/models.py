from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Resume(models.Model):
    """A resume record belonging to a user."""

    COUNTRY_CHOICES = [
        ("us", "United States"),
        ("uk", "United Kingdom"),
        ("eu", "Europe / EU"),
        ("in", "India"),
        ("ca", "Canada"),
        ("au", "Australia"),
        ("ae", "UAE / Middle East"),
        ("sg", "Singapore"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="resumes")
    title = models.CharField(max_length=200, default="My Resume")
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=200, blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    portfolio = models.URLField(blank=True)
    target_country = models.CharField(max_length=10, choices=COUNTRY_CHOICES, default="us")
    target_role = models.CharField(max_length=200, blank=True)
    professional_summary = models.TextField(blank=True)
    template_style = models.CharField(
        max_length=20,
        choices=[
            ("modern", "Modern"),
            ("classic", "Classic"),
            ("minimal", "Minimal"),
            ("creative", "Creative"),
            ("executive", "Executive"),
        ],
        default="modern",
        help_text="Visual template style used when previewing/exporting this resume.",
    )
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title} — {self.full_name}"

    TEMPLATE_STYLE_CHOICES = [
        ("modern", "Modern"),
        ("classic", "Classic"),
        ("minimal", "Minimal"),
        ("creative", "Creative"),
        ("executive", "Executive"),
    ]


class ResumeUpload(models.Model):
    """An existing resume file (PDF/DOCX) uploaded by a user to rebuild or update a resume."""

    FILE_TYPE_CHOICES = [
        ("pdf", "PDF"),
        ("docx", "DOCX"),
        ("doc", "DOC"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("parsed", "Parsed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="resume_uploads")
    file = models.FileField(upload_to="resume_uploads/")
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    extracted_text = models.TextField(blank=True, help_text="Raw text extracted from the uploaded file.")
    parsed_data = models.JSONField(default=dict, blank=True, help_text="Structured resume data parsed from the file.")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    parse_error = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.original_filename} — {self.user.username}"


class Experience(models.Model):
    """Work experience entry."""

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="experiences")
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    role = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    tech_stack = models.CharField(max_length=500, blank=True, help_text="Comma-separated technologies")
    description = models.TextField(blank=True, help_text="Role summary paragraph")
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "-start_date"]

    def __str__(self):
        return f"{self.role} at {self.company}"


class ExperienceBullet(models.Model):
    """Bullet point under an experience."""

    experience = models.ForeignKey(Experience, on_delete=models.CASCADE, related_name="bullets")
    text = models.TextField()
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.text[:80]


class Education(models.Model):
    """Education entry."""

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="education")
    degree = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    grade = models.CharField(max_length=50, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "-end_date"]

    def __str__(self):
        return f"{self.degree} — {self.institution}"


class Skill(models.Model):
    """Skill entry categorized."""

    CATEGORY_CHOICES = [
        ("backend", "Backend"),
        ("frontend", "Frontend"),
        ("database", "Database"),
        ("cloud", "Cloud & DevOps"),
        ("tools", "Tools & Platforms"),
        ("ai_ml", "AI / ML / Agents"),
        ("languages", "Languages"),
        ("soft", "Soft Skills"),
    ]

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="skills")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    name = models.CharField(max_length=100)
    proficiency = models.CharField(max_length=50, blank=True, help_text="e.g. Expert, Advanced, Familiar")
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["category", "display_order", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Project(models.Model):
    """Project entry."""

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=200)
    description = models.TextField()
    technologies = models.CharField(max_length=300, blank=True)
    link = models.URLField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "-start_date"]

    def __str__(self):
        return self.name


class Certification(models.Model):
    """Certification entry."""

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="certifications")
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    date = models.DateField(null=True, blank=True)
    link = models.URLField(blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "-date"]

    def __str__(self):
        return f"{self.name} — {self.issuer}"


class JobDescription(models.Model):
    """Stored job description for targeted resume generation."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="job_descriptions")
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)
    raw_text = models.TextField()
    extracted_keywords = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.company}"


class ResumeVersion(models.Model):
    """Snapshot version of a resume for A/B testing and rollback."""

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField(default=1)
    name = models.CharField(max_length=200)
    snapshot = models.JSONField(default=dict, help_text="Full resume data snapshot")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-version_number"]
        unique_together = ["resume", "version_number"]

    def __str__(self):
        return f"{self.resume.title} v{self.version_number}"