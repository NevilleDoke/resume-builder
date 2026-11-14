from django import forms
from .models import Resume, Experience, ExperienceBullet, Education, Skill, Project, Certification, JobDescription, ResumeUpload


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = [
            "title", "full_name", "email", "phone", "location",
            "linkedin", "github", "portfolio", "target_country",
            "target_role", "template_style", "professional_summary", "is_default",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"}),
            "full_name": forms.TextInput(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"}),
            "email": forms.EmailInput(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"}),
            "phone": forms.TextInput(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"}),
            "location": forms.TextInput(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"}),
            "linkedin": forms.URLInput(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"}),
            "github": forms.URLInput(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"}),
            "portfolio": forms.URLInput(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"}),
            "target_country": forms.Select(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"}),
            "target_role": forms.TextInput(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"}),
            "template_style": forms.Select(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"}),
            "professional_summary": forms.Textarea(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none", "rows": 4}),
            "is_default": forms.CheckboxInput(attrs={"class": "w-4 h-4 text-blue-600 rounded focus:ring-blue-500"}),
        }


class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ["company", "location", "role", "start_date", "end_date", "is_current", "tech_stack", "description"]
        widgets = {
            "company": forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "location": forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "role": forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "is_current": forms.CheckboxInput(attrs={"class": "w-4 h-4 text-blue-600 rounded focus:ring-blue-500"}),
            "tech_stack": forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none", "placeholder": "Django, FastAPI, Python, PostgreSQL"}),
            "description": forms.Textarea(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none", "rows": 3}),
        }


class ExperienceBulletForm(forms.ModelForm):
    class Meta:
        model = ExperienceBullet
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none", "rows": 2, "placeholder": "e.g. Designed RESTful APIs serving 10K+ requests/min"}),
        }


class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ["degree", "institution", "location", "start_date", "end_date", "grade"]
        widgets = {
            "degree": forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "institution": forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "location": forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "grade": forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
        }


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["category", "name", "proficiency"]
        widgets = {
            "category": forms.Select(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "name": forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "proficiency": forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none", "placeholder": "Expert / Advanced / Familiar"}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "technologies", "link", "start_date", "end_date"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "description": forms.Textarea(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none", "rows": 3}),
            "technologies": forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none", "placeholder": "Django, FastAPI, React, AWS"}),
            "link": forms.URLInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
        }


class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ["name", "issuer", "date", "link"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "issuer": forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
            "link": forms.URLInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"}),
        }


class JobDescriptionForm(forms.ModelForm):
    class Meta:
        model = JobDescription
        fields = ["title", "company", "raw_text"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"}),
            "company": forms.TextInput(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"}),
            "raw_text": forms.Textarea(attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none", "rows": 10, "placeholder": "Paste the full job description here..."}),
        }


class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = ResumeUpload
        fields = ["file"]
        widgets = {
            "file": forms.ClearableFileInput(attrs={"class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"}),
        }

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if not f:
            raise forms.ValidationError("Please select a file to upload.")
        ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
        if ext not in ("pdf", "docx", "doc"):
            raise forms.ValidationError("Only PDF, DOCX, and DOC files are supported.")
        if f.size > 10 * 1024 * 1024:
            raise forms.ValidationError("File is too large (max 10 MB).")
        return f