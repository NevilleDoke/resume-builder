
"""
DOCX and PDF export generators for resumes.
"""
from io import BytesIO

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle,
)
from reportlab.lib import colors

ACCENT_COLOR = RGBColor(0x1F, 0x2A, 0x44)
SECONDARY_COLOR = RGBColor(0x2E, 0x5A, 0x88)
LIGHT_GRAY = RGBColor(0x6B, 0x72, 0x80)

ACCENT_HEX = "#1F2A44"
SECONDARY_HEX = "#2E5A88"
LIGHT_HEX = "#6B7280"


def _set_cell_background(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tcPr.append(shd)


def generate_docx(resume):
    doc = Document()

    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)
    section.top_margin = Inches(0.6)
    section.bottom_margin = Inches(0.6)

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)

    name_para = doc.add_paragraph()
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = name_para.add_run(resume.full_name.upper())
    run.bold = True
    run.font.size = Pt(22)
    run.font.color.rgb = ACCENT_COLOR

    contact_parts = [resume.email, resume.phone, resume.location]
    contact_line = "  |  ".join(p for p in contact_parts if p)
    if resume.linkedin:
        contact_line += "  |  LinkedIn: " + resume.linkedin
    if resume.github:
        contact_line += "  |  GitHub: " + resume.github
    contact_para = doc.add_paragraph()
    contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = contact_para.add_run(contact_line)
    run.font.size = Pt(9)
    run.font.color.rgb = LIGHT_GRAY

    if resume.target_role:
        role_para = doc.add_paragraph()
        role_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = role_para.add_run(resume.target_role.upper())
        run.bold = True
        run.font.size = Pt(11)
        run.font.color.rgb = SECONDARY_COLOR

    hr = doc.add_paragraph()
    pPr = hr._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "1F2A44")
    pBdr.append(bottom)
    pPr.append(pBdr)

    if resume.professional_summary:
        _add_section_heading(doc, "PROFESSIONAL SUMMARY")
        p = doc.add_paragraph()
        p.add_run(resume.professional_summary)
        p.paragraph_format.space_after = Pt(6)

    if resume.experiences.exists():
        _add_section_heading(doc, "PROFESSIONAL EXPERIENCE")
        for exp in resume.experiences.all():
            line = doc.add_paragraph()
            run = line.add_run(exp.role.upper() + " — " + exp.company)
            run.bold = True
            run.font.size = Pt(11)
            run.font.color.rgb = ACCENT_COLOR

            date_str = exp.start_date.strftime("%b %Y")
            if exp.end_date:
                date_str += " — " + exp.end_date.strftime("%b %Y")
            else:
                date_str += " — Present"
            loc = " | " + exp.location if exp.location else ""
            meta = doc.add_paragraph()
            run = meta.add_run(date_str + loc)
            run.italic = True
            run.font.size = Pt(9.5)
            run.font.color.rgb = LIGHT_GRAY

            if exp.tech_stack:
                tech = doc.add_paragraph()
                run = tech.add_run("Tech Stack: ")
                run.bold = True
                run.font.size = Pt(9)
                run.font.color.rgb = SECONDARY_COLOR
                run = tech.add_run(exp.tech_stack)
                run.font.size = Pt(9)
                run.font.color.rgb = LIGHT_GRAY

            if exp.description:
                desc = doc.add_paragraph()
                desc.add_run(exp.description)
                desc.paragraph_format.space_after = Pt(2)

            for bullet in exp.bullets.all():
                bp = doc.add_paragraph(style="List Bullet")
                bp.add_run(bullet.text)
                bp.paragraph_format.space_after = Pt(1)
                bp.paragraph_format.left_indent = Inches(0.25)

            spacer = doc.add_paragraph()
            spacer.paragraph_format.space_after = Pt(4)

    if resume.education.exists():
        _add_section_heading(doc, "EDUCATION")
        for edu in resume.education.all():
            p = doc.add_paragraph()
            run = p.add_run(edu.degree + " — " + edu.institution)
            run.bold = True
            run.font.size = Pt(10.5)

            date_parts = []
            if edu.start_date:
                date_parts.append(edu.start_date.strftime("%b %Y"))
            if edu.end_date:
                date_parts.append(edu.end_date.strftime("%b %Y"))
            if date_parts:
                meta = " — ".join(date_parts)
                if edu.location:
                    meta += " | " + edu.location
                mp = doc.add_paragraph()
                run = mp.add_run(meta)
                run.italic = True
                run.font.size = Pt(9)
                run.font.color.rgb = LIGHT_GRAY
            if edu.grade:
                gp = doc.add_paragraph()
                run = gp.add_run("Grade: " + edu.grade)
                run.font.size = Pt(9)
                run.font.color.rgb = LIGHT_GRAY

    if resume.skills.exists():
        _add_section_heading(doc, "SKILLS")
        cats = {}
        for skill in resume.skills.all():
            cats.setdefault(skill.get_category_display(), []).append(skill)
        for cat, skills in cats.items():
            p = doc.add_paragraph()
            run = p.add_run(cat + ": ")
            run.bold = True
            run.font.size = Pt(10)
            run.font.color.rgb = SECONDARY_COLOR
            skill_text = ", ".join(s.name for s in skills)
            run = p.add_run(skill_text)
            run.font.size = Pt(10)

    if resume.projects.exists():
        _add_section_heading(doc, "PROJECTS")
        for proj in resume.projects.all():
            p = doc.add_paragraph()
            run = p.add_run(proj.name)
            run.bold = True
            run.font.size = Pt(10.5)
            run.font.color.rgb = ACCENT_COLOR
            if proj.technologies:
                tp = doc.add_paragraph()
                run = tp.add_run("Technologies: " + proj.technologies)
                run.font.size = Pt(9)
                run.font.color.rgb = LIGHT_GRAY
            desc_p = doc.add_paragraph()
            desc_p.add_run(proj.description)
            desc_p.paragraph_format.space_after = Pt(2)

    if resume.certifications.exists():
        _add_section_heading(doc, "CERTIFICATIONS")
        for cert in resume.certifications.all():
            p = doc.add_paragraph()
            run = p.add_run(cert.name + " — " + cert.issuer)
            run.bold = True
            run.font.size = Pt(10)
            if cert.date:
                run = p.add_run(" (" + cert.date.strftime("%b %Y") + ")")
                run.font.size = Pt(9)
                run.font.color.rgb = LIGHT_GRAY

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()


def _add_section_heading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = ACCENT_COLOR
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), "1F2A44")
    pBdr.append(bottom)
    pPr.append(pBdr)


def _pdf_styles():
    return {
        "name": ParagraphStyle(
            "name", fontName="Helvetica-Bold", fontSize=20,
            textColor=HexColor(ACCENT_HEX), alignment=TA_CENTER, spaceAfter=2,
        ),
        "title": ParagraphStyle(
            "title", fontName="Helvetica-Bold", fontSize=10.5,
            textColor=HexColor(SECONDARY_HEX), alignment=TA_CENTER,
            spaceAfter=8, tracking=1,
        ),
        "contact": ParagraphStyle(
            "contact", fontName="Helvetica", fontSize=8.5,
            textColor=HexColor(LIGHT_HEX), alignment=TA_CENTER, spaceAfter=10,
        ),
        "section": ParagraphStyle(
            "section", fontName="Helvetica-Bold", fontSize=11,
            textColor=HexColor(ACCENT_HEX), spaceBefore=14, spaceAfter=5,
        ),
        "role": ParagraphStyle(
            "role", fontName="Helvetica-Bold", fontSize=11,
            textColor=HexColor(ACCENT_HEX), spaceAfter=1,
        ),
        "company": ParagraphStyle(
            "company", fontName="Helvetica-Bold", fontSize=10,
            textColor=HexColor(SECONDARY_HEX), spaceAfter=1,
        ),
        "meta": ParagraphStyle(
            "meta", fontName="Helvetica-Oblique", fontSize=8.5,
            textColor=HexColor(LIGHT_HEX), spaceAfter=3,
        ),
        "tech": ParagraphStyle(
            "tech", fontName="Helvetica-Bold", fontSize=8.5,
            textColor=HexColor(SECONDARY_HEX), spaceAfter=2,
        ),
        "desc": ParagraphStyle(
            "desc", fontName="Helvetica", fontSize=9.5,
            textColor=colors.HexColor("#374151"), spaceAfter=4, leading=13,
        ),
        "bullet": ParagraphStyle(
            "bullet", fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#374151"), leftIndent=14,
            spaceAfter=2, leading=12,
        ),
        "edu_degree": ParagraphStyle(
            "edu_degree", fontName="Helvetica-Bold", fontSize=10,
            textColor=HexColor(ACCENT_HEX), spaceAfter=1,
        ),
        "edu_inst": ParagraphStyle(
            "edu_inst", fontName="Helvetica", fontSize=9.5,
            textColor=HexColor(SECONDARY_HEX), spaceAfter=1,
        ),
        "skill_cat": ParagraphStyle(
            "skill_cat", fontName="Helvetica-Bold", fontSize=9,
            textColor=HexColor(SECONDARY_HEX), spaceAfter=2,
        ),
        "skill_list": ParagraphStyle(
            "skill_list", fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#374151"), spaceAfter=3, leading=12,
        ),
    }


def generate_pdf(resume):
    """Generate a professional PDF resume using ReportLab."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=resume.full_name + " - Resume",
        author=resume.full_name,
    )
    styles = _pdf_styles()
    story = []

    # Header
    story.append(Paragraph(resume.full_name.upper(), styles["name"]))
    story.append(Paragraph(resume.target_role.upper(), styles["title"]))

    contact_parts = [resume.email, resume.phone, resume.location]
    contact_line = "  |  ".join(p for p in contact_parts if p)
    if resume.linkedin:
        contact_line += "  |  LinkedIn: " + resume.linkedin
    if resume.github:
        contact_line += "  |  GitHub: " + resume.github
    story.append(Paragraph(contact_line, styles["contact"]))
    story.append(HRFlowable(width="100%", thickness=1.2, color=HexColor(ACCENT_HEX), spaceAfter=10))

    # Professional Summary
    if resume.professional_summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", styles["section"]))
        story.append(HRFlowable(width="100%", thickness=0.7, color=HexColor(ACCENT_HEX), spaceAfter=6))
        story.append(Paragraph(resume.professional_summary, styles["desc"]))

    # Professional Experience
    if resume.experiences.exists():
        story.append(Paragraph("PROFESSIONAL EXPERIENCE", styles["section"]))
        story.append(HRFlowable(width="100%", thickness=0.7, color=HexColor(ACCENT_HEX), spaceAfter=6))
        for exp in resume.experiences.all():
            story.append(Paragraph(exp.role.upper() + " — " + exp.company, styles["role"]))
            date_str = exp.start_date.strftime("%b %Y")
            if exp.end_date:
                date_str += " — " + exp.end_date.strftime("%b %Y")
            else:
                date_str += " — Present"
            loc = " | " + exp.location if exp.location else ""
            story.append(Paragraph(date_str + loc, styles["meta"]))
            if exp.tech_stack:
                story.append(Paragraph("Tech Stack: " + exp.tech_stack, styles["tech"]))
            if exp.description:
                story.append(Paragraph(exp.description, styles["desc"]))
            for bullet in exp.bullets.all():
                story.append(Paragraph("• " + bullet.text, styles["bullet"]))
            story.append(Spacer(1, 4))

    # Education
    if resume.education.exists():
        story.append(Paragraph("EDUCATION", styles["section"]))
        story.append(HRFlowable(width="100%", thickness=0.7, color=HexColor(ACCENT_HEX), spaceAfter=6))
        for edu in resume.education.all():
            story.append(Paragraph(edu.degree + " — " + edu.institution, styles["edu_degree"]))
            date_parts = []
            if edu.start_date:
                date_parts.append(edu.start_date.strftime("%b %Y"))
            if edu.end_date:
                date_parts.append(edu.end_date.strftime("%b %Y"))
            if date_parts:
                meta = " — ".join(date_parts)
                if edu.location:
                    meta += " | " + edu.location
                story.append(Paragraph(meta, styles["meta"]))
            if edu.grade:
                story.append(Paragraph("Grade: " + edu.grade, styles["meta"]))

    # Skills
    if resume.skills.exists():
        story.append(Paragraph("SKILLS", styles["section"]))
        story.append(HRFlowable(width="100%", thickness=0.7, color=HexColor(ACCENT_HEX), spaceAfter=6))
        cats = {}
        for skill in resume.skills.all():
            cats.setdefault(skill.get_category_display(), []).append(skill)
        for cat, skills in cats.items():
            story.append(Paragraph(cat + ": ", styles["skill_cat"]))
            skill_text = ", ".join(s.name for s in skills)
            story.append(Paragraph(skill_text, styles["skill_list"]))

    # Projects
    if resume.projects.exists():
        story.append(Paragraph("PROJECTS", styles["section"]))
        story.append(HRFlowable(width="100%", thickness=0.7, color=HexColor(ACCENT_HEX), spaceAfter=6))
        for proj in resume.projects.all():
            story.append(Paragraph(proj.name, styles["role"]))
            if proj.technologies:
                story.append(Paragraph("Technologies: " + proj.technologies, styles["tech"]))
            story.append(Paragraph(proj.description, styles["desc"]))

    # Certifications
    if resume.certifications.exists():
        story.append(Paragraph("CERTIFICATIONS", styles["section"]))
        story.append(HRFlowable(width="100%", thickness=0.7, color=HexColor(ACCENT_HEX), spaceAfter=6))
        for cert in resume.certifications.all():
            cert_line = cert.name + " — " + cert.issuer
            if cert.date:
                cert_line += " (" + cert.date.strftime("%b %Y") + ")"
            story.append(Paragraph(cert_line, styles["role"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
