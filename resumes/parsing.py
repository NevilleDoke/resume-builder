"""
Text extraction and heuristic parsing for uploaded resume files (PDF / DOCX).

The extracted data is never perfect - resumes have no standard format - so the
parser stores the raw extracted text as well and lets the user review and edit
everything in the builder before saving.
"""
import os
import re
from datetime import datetime, date
import zipfile

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(
    r"(\+?\d{1,3}[\s\-.]?)?(\(?\d{3}\)?[\s\-.]?)?\d{3}[\s\-.]?\d{4}"
)
URL_RE = re.compile(r"https?://[^\s)+>;]+")
DATE_LINE_RE = re.compile(
    r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{2,4}\b"
    r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
    r"|\b(19|20)\d{2}\b"
)
DATE_RANGE_RE = re.compile(
    r"("
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{2,4}"
    r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|\b(19|20)\d{2}\b"
    r")\s*([\u2013\u2014-]|to)\s*("
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{2,4}"
    r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|Present|Current|\b(19|20)\d{2}\b"
    r")",
    re.IGNORECASE,
)

SECTION_HEADERS = {
    "summary": [
        "professional summary", "summary", "career objective", "objective",
        "profile", "professional profile",
    ],
    "experience": [
        "professional experience", "experience", "work experience",
        "employment history", "work history", "career history",
    ],
    "education": ["education", "academic background", "qualifications"],
    "skills": ["skills", "technical skills", "technologies", "core competencies"],
    "projects": ["projects", "key projects", "selected projects"],
    "certifications": ["certifications", "certificates", "licenses", "certification"],
}

SECTION_KEYWORDS = sorted(
    [kw for keys in SECTION_HEADERS.values() for kw in keys], key=len, reverse=True
)
SECTION_RE = re.compile(
    r"^\s*(" + "|".join(re.escape(k) for k in SECTION_KEYWORDS) + r")\s*:?\s*$",
    re.IGNORECASE,
)


def parse_date(value):
    """Best-effort conversion of a free-text date string into a date.

    Returns None when the value cannot be parsed (callers should treat it as
    unknown / not set).
    """
    if not value:
        return None
    v = str(value).strip()
    if not v or v.lower() in ("present", "current", "ongoing"):
        return None
    for fmt in ("%Y-%m-%d", "%b %Y", "%B %Y", "%m/%d/%Y", "%d/%m/%Y", "%Y", "%b %y"):
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    m = re.search(r"\b(19|20)\d{2}\b", v)
    if m:
        return date(int(m.group(0)), 1, 1)
    return None


def _clean_lines(text):
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if line:
            lines.append(line)
    return lines


def extract_text_from_pdf(path):
    """Extract text from a PDF file at ``path`` using pypdf (with fallbacks)."""
    errors = []

    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(path)
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        text = "\n".join(parts)
        if text.strip():
            return text
    except Exception as exc:  # pragma: no cover - depends on environment
        errors.append("pypdf: " + str(exc))

    try:
        from PyPDF2 import PdfReader  # type: ignore

        reader = PdfReader(path)
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        text = "\n".join(parts)
        if text.strip():
            return text
    except Exception as exc:  # pragma: no cover - depends on environment
        errors.append("PyPDF2: " + str(exc))

    # Last-resort built-in extractor for uncompressed PDF text streams.
    return _extract_pdf_text_builtin(path, errors)


def _extract_pdf_text_builtin(path, errors):
    """Very best-effort PDF text extraction without third-party libraries.

    Handles uncompressed FlateDecode streams only, so scanned or heavily
    compressed PDFs may yield little or no text.
    """
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        errors.append("builtin: cannot read file: " + str(exc))
        return ""

    # Decompress obvious zlib streams found inside the file.
    try:
        import zlib  # standard library

        decompressed = zlib.decompress(data)
        text_source = decompressed.decode("latin-1", errors="ignore")
    except Exception:
        text_source = data.decode("latin-1", errors="ignore")

    texts = []
    # Inline text-showing operators: (string) Tj and [ ... ] TJ
    for m in re.finditer(r"\(([^()]*)\)\s*Tj", text_source):
        texts.append(m.group(1))
    for m in re.finditer(r"\[(.*?)\]\s*TJ", text_source, re.S):
        chunk = m.group(1)
        for part in re.findall(r"\(([^()]*)\)", chunk):
            texts.append(part)
    return "\n".join(texts)


def extract_text_from_docx(path):
    """Extract text from a DOCX file at ``path`` using python-docx."""
    from docx import Document  # type: ignore

    doc = Document(path)
    parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text)
    return "\n".join(parts)


def extract_text_from_file(path, file_type):
    """Dispatch to the right extractor based on file type."""
    if file_type == "docx":
        return extract_text_from_docx(path)
    # "doc" and "pdf" both go through the PDF path as best effort;
    # legacy binary .doc files usually yield little text this way.
    return extract_text_from_pdf(path)


def _looks_like_name(line):
    if not line or len(line) > 60:
        return False
    if EMAIL_RE.search(line) or URL_RE.search(line):
        return False
    if re.search(r"\d", line):
        return False
    if SECTION_RE.search(line):
        return False
    words = [w for w in line.split() if re.search(r"[A-Za-z]", w)]
    if len(words) < 2 or len(words) > 5:
        return False
    return all(re.fullmatch(r"[A-Za-z.\-&']+", w) for w in words)


def _extract_contact(text):
    emails = EMAIL_RE.findall(text)
    phone = ""
    for m in PHONE_RE.finditer(text):
        candidate = re.sub(r"\s+", " ", m.group(0)).strip()
        if len(re.sub(r"\D", "", candidate)) >= 7:
            phone = candidate
            break
    linkedin = github = portfolio = None
    for m in URL_RE.finditer(text):
        url = m.group(0).rstrip(".,);")
        low = url.lower()
        if "linkedin.com" in low:
            linkedin = url
        elif "github.com" in low:
            github = url
        elif any(d in low for d in ("portfolio", "behance.net", "dribbble.com", "personal")):
            portfolio = url
    # Bare domains without a scheme (e.g. linkedin.com/in/name).
    if not linkedin:
        m = re.search(r"\blinkedin\.com/in/[A-Za-z0-9.\-_/]+", text, re.I)
        if m:
            linkedin = m.group(0).rstrip(".,);")
    if not github:
        m = re.search(r"\bgithub\.com/[A-Za-z0-9.\-_/]+", text, re.I)
        if m:
            github = m.group(0).rstrip(".,);")
    return emails[0] if emails else "", phone, linkedin or "", github or "", portfolio or ""


def _split_into_sections(lines):
    """Return list of (section_key, [lines]) tuples."""
    sections = []
    current = "header"
    current_lines = []
    for line in lines:
        if SECTION_RE.search(line):
            if current_lines:
                sections.append((current, current_lines))
            key = "header"
            for k, aliases in SECTION_HEADERS.items():
                if line.strip().lower().rstrip(":") in [a.lower() for a in aliases]:
                    key = k
                    break
            current = key
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current, current_lines))
    return sections


def _split_dates(date_str):
    parts = re.split(r"\s*([\u2013\u2014-]|to)\s*", date_str, flags=re.I)
    flat = [p.strip() for p in parts if p.strip() and p.strip() not in ("\u2013", "\u2014", "-", "to", "To")]
    if not flat:
        return "", ""
    return flat[0], flat[-1] if len(flat) > 1 else ""


def _split_role_company(pre):
    role, company = "", ""
    for sep in ("\u2014", "\u2013", "—", " - ", " at ", " | ", "-"):
        if sep in pre:
            parts = [p.strip() for p in pre.split(sep, 1)]
            role = parts[0]
            company = parts[1] if len(parts) > 1 else ""
            break
    if not role and pre:
        role = pre
    return role, company


def _parse_experience_block(lines):
    entries = []
    current = None
    header_lines = []  # role / company lines seen before the entry's date line

    def finalize():
        nonlocal current, header_lines
        if current is not None:
            entries.append(current)
            current = None
        elif header_lines:
            # Role line seen without a following date line.
            header = " ".join(header_lines)
            role, company = _split_role_company(header)
            entries.append({
                "role": role,
                "company": company,
                "location": "",
                "start_date": "",
                "end_date": "",
                "tech_stack": "",
                "description": "",
                "bullets": [],
                "is_current": False,
            })
            header_lines = []

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        m = DATE_RANGE_RE.search(stripped)
        is_date_line = bool(m and re.search(r"[A-Za-z]", stripped))
        if is_date_line:
            # A date line starts (or ends) an experience entry.
            entry_header = list(header_lines)
            header_lines = []
            finalize()
            date_str = m.group(0)
            pre = stripped[: m.start()] + stripped[m.end() :]
            location = ""
            if " | " in pre:
                pre, location = [p.strip() for p in pre.split(" | ", 1)]
            pre = pre.strip(" -|–—:")
            # Anything buffered before the date line is role/company text.
            if entry_header:
                header = " ".join(entry_header)
                role, company = _split_role_company(header)
                if not role and pre:
                    role = pre
                    pre = ""
            else:
                role, company = _split_role_company(pre)
            start_date, end_date = _split_dates(date_str)
            current = {
                "role": role,
                "company": company,
                "location": location,
                "start_date": start_date,
                "end_date": end_date,
                "tech_stack": "",
                "description": "",
                "bullets": [],
                "is_current": bool(re.search(r"present|current", end_date, re.I)),
            }
            header_lines = []
            continue
        if current is None:
            header_lines.append(stripped)
            continue
        low = stripped.lower()
        if stripped[0] in ("\u2022", "-", "*", "•") or stripped.startswith(("- ", "* ")):
            current["bullets"].append(stripped.lstrip("\u2022-*. ").strip())
            continue
        if low.startswith("tech stack") or low.startswith("technologies"):
            current["tech_stack"] = re.sub(r"^(tech stack|technologies)[:\-]\s*", "", stripped, flags=re.I)
            continue
        # A role line like "Role — Company" without a date starts a new entry.
        if (
            len(stripped) < 90
            and not DATE_RANGE_RE.search(stripped)
            and re.search(r"\s(—|\u2014|\u2013| at | \| )\s", stripped)
        ):
            finalize()
            header_lines = [stripped]
            continue
        if not current.get("role"):
            current["role"] = stripped
            continue
        if not current.get("company"):
            current["company"] = stripped
            continue
        current["description"] = (
            (current.get("description") + " ") if current.get("description") else ""
        ) + stripped
    finalize()

    cleaned = []
    for entry in entries:
        role = entry.get("role", "")
        company = entry.get("company", "")
        for sep in ("\u2014", "\u2013", "—", "-", " | ", " at "):
            if sep in role and not company:
                parts = [p.strip() for p in role.split(sep, 1)]
                role, company = parts[0], parts[1]
        entry["role"] = role
        entry["company"] = company
        cleaned.append(entry)
    return cleaned


def _parse_simple_list(lines, skip_prefixes=("tech stack", "technologies")):
    items = []
    for line in lines:
        low = line.lower().strip()
        if not low:
            continue
        if low.startswith(skip_prefixes):
            continue
        items.append(line.strip())
    return items


def parse_resume_text(text):
    """Parse free-text resume content into a structured dictionary."""
    if not text:
        return {}

    lines = _clean_lines(text)
    data = {
        "full_name": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "github": "",
        "portfolio": "",
        "target_role": "",
        "professional_summary": "",
        "experiences": [],
        "education": [],
        "skills": [],
        "projects": [],
        "certifications": [],
    }

    email, phone, linkedin, github, portfolio = _extract_contact(text)
    data["email"] = email
    data["phone"] = phone
    data["linkedin"] = linkedin or ""
    data["github"] = github or ""
    data["portfolio"] = portfolio or ""

    # Name: first plausible line of the document.
    for line in lines[:8]:
        if _looks_like_name(line):
            data["full_name"] = line
            break

    sections = _split_into_sections(lines)
    section_map = {}
    for key, sec_lines in sections:
        section_map.setdefault(key, []).extend(sec_lines)

    # Professional summary / objective.
    summary_lines = section_map.get("summary", [])
    # Skip lines that are just contact info inside the summary block.
    summary_lines = [l for l in summary_lines if not EMAIL_RE.search(l) and not URL_RE.search(l)]
    if summary_lines:
        data["professional_summary"] = " ".join(summary_lines)

    # Target role: first capitalised line right under the name/header area if present.
    header_lines = section_map.get("header", [])
    for line in header_lines[:6]:
        if line == data.get("full_name"):
            continue
        if len(line) < 60 and not EMAIL_RE.search(line) and not PHONE_RE.search(line):
            data["target_role"] = line
            break

    # Experience.
    data["experiences"] = _parse_experience_block(section_map.get("experience", []))

    # Education (simple lines).
    data["education"] = [
        {"degree": "", "institution": line, "location": "", "start_date": "",
         "end_date": "", "grade": ""}
        for line in _parse_simple_list(section_map.get("education", []))
    ]

    # Skills: split comma/line separated entries.
    skills = []
    for line in section_map.get("skills", []):
        for part in re.split(r",|\|", line):
            part = part.strip(" -•")
            if part:
                skills.append({"category": "backend", "name": part, "proficiency": ""})
    data["skills"] = skills

    # Projects and certifications (simple lists).
    data["projects"] = [
        {"name": line, "description": "", "technologies": "", "link": "",
         "start_date": "", "end_date": ""}
        for line in _parse_simple_list(section_map.get("projects", []))
    ]
    data["certifications"] = [
        {"name": line, "issuer": "", "date": "", "link": ""}
        for line in _parse_simple_list(section_map.get("certifications", []))
    ]

    return data
