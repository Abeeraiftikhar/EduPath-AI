import io
import json
import re
import zipfile
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from core.schemas import CoursePackage
from core.utils import mcq_answer_index


# --------------------------------------------------------------------- Markdown
def _request_lines(course: CoursePackage):
    return [f"- **{k.replace('_', ' ').title()}:** {v}" for k, v in course.request.model_dump().items()]


def _lesson_md(course: CoursePackage):
    lines = []
    for l in course.lessons.lessons:
        lines += [f"### Lesson {l.module_number}.{l.lesson_number}: {l.title}", "", l.notes, ""]
        if l.examples:
            lines += ["**Examples:**"] + [f"- {x}" for x in l.examples] + [""]
        if l.exercises:
            lines += ["**Exercises:**"] + [f"- {x}" for x in l.exercises] + [""]
        if l.case_study:
            lines += [f"**Case study:** {l.case_study}", ""]
    return lines


def _assessment_md(course: CoursePackage, with_answers=True):
    lines = []
    for a in course.assessments.items:
        lines += [f"### {a.type.upper()}: {a.title}", "", a.prompt, ""]
        lines += [f"{chr(65 + i)}. {o}" for i, o in enumerate(a.options)]
        if a.options:
            lines.append("")
        if with_answers:
            lines.append(f"**Answer:** {_answer_text(a)}")
        lines.append(f"**Mapped objective:** {a.learning_objective}")
        if a.rubric and with_answers:
            lines.append(f"**Rubric:** {a.rubric}")
        lines.append("")
    return lines


def _answer_text(a) -> str:
    """'B' -> 'B. <option text>' so the key is readable on its own."""
    index = mcq_answer_index(a.answer, a.options) if a.options else -1
    return f"{chr(65 + index)}. {a.options[index]}" if index >= 0 else a.answer


def build_markdown(course: CoursePackage) -> str:
    c, v = course.curriculum, course.validation
    lines = [f"# {c.title}", "", c.description, "", "## Course Request", ""] + _request_lines(course)
    if c.prerequisites:
        lines += ["", "## Prerequisites", ""] + [f"- {p}" for p in c.prerequisites]
    if c.roadmap:
        lines += ["", "## Roadmap", ""] + [f"- {r}" for r in c.roadmap]
    lines += ["", "## Curriculum", ""]
    for m in c.modules:
        lines += [f"### Module {m.number}: {m.title}", m.summary, "", "**Learning objectives:**"]
        lines += [f"- {x}" for x in m.learning_objectives] + [""]
    lines += ["## Lessons", ""] + _lesson_md(course)
    lines += ["## Assessments", ""] + _assessment_md(course)
    lines += ["## Validation", "", f"**Status:** {v.status}  ", f"**Score:** {v.score}%  ",
              f"**Attempts:** {v.attempts}", ""]
    lines += [f"- {'PASS' if k.passed else 'FAIL'} - {k.name}" + (f" ({k.detail})" if k.detail else "") for k in v.checks]
    return "\n".join(lines) + "\n"


def build_lessons_markdown(course: CoursePackage) -> str:
    return "\n".join([f"# Lessons - {course.curriculum.title}", ""] + _lesson_md(course)) + "\n"


def build_answer_key_markdown(course: CoursePackage) -> str:
    lines = [f"# Answer Key & Rubrics - {course.curriculum.title}", ""] + _assessment_md(course)
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------------- PDF
def _rich(text: str) -> str:
    """Escape for ReportLab's mini-XML, then turn **bold** and *italic* Markdown into tags."""
    safe = escape(text or "")
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
    return re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", safe)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(.65 * inch, .4 * inch, "EduPath-AI - generated course package")
    canvas.drawRightString(A4[0] - .65 * inch, .4 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(course: CoursePackage) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=.65 * inch, leftMargin=.65 * inch,
                            topMargin=.65 * inch, bottomMargin=.75 * inch, title=course.curriculum.title)
    styles = getSampleStyleSheet()
    styles["Title"].alignment = TA_CENTER
    styles["Title"].textColor = colors.HexColor("#172554")
    for name in ("Heading1", "Heading2", "Heading3"):
        styles[name].textColor = colors.HexColor("#1D4ED8")
    body, bullet = styles["BodyText"], ParagraphStyle("b", parent=styles["BodyText"], leftIndent=14, bulletIndent=4)
    small = ParagraphStyle("s", parent=body, textColor=colors.HexColor("#64748B"), fontSize=9, alignment=TA_CENTER)
    c, v = course.curriculum, course.validation

    def p(text, style=body):
        return Paragraph(_rich(text), style)

    def bullets(items):
        return [Paragraph(_rich(x), bullet, bulletText="•") for x in items]

    def md_block(text):
        """Render lesson notes: ### headings, - bullets, paragraphs."""
        out = []
        for line in (text or "").splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                out.append(p(line.lstrip("# "), styles["Heading3"]))
            elif line.startswith(("- ", "* ")):
                out += bullets([line[2:]])
            else:
                out.append(p(line))
        return out

    story = [Spacer(1, 1.3 * inch), p(c.title, styles["Title"]), Spacer(1, 10), p(c.description, body), Spacer(1, 14)]
    for k, val in course.request.model_dump().items():
        story.append(p(f"**{k.replace('_', ' ').title()}:** {val}"))
    story += [Spacer(1, 14), p(f"Quality check: {v.status} - {v.score}% of checks passed", small), PageBreak()]

    story.append(p("Curriculum", styles["Heading1"]))
    if c.prerequisites:
        story += [p("Prerequisites", styles["Heading3"])] + bullets(c.prerequisites)
    if c.roadmap:
        story += [p("Roadmap", styles["Heading3"])] + bullets(c.roadmap)
    for m in c.modules:
        story += [p(f"Module {m.number}: {m.title}", styles["Heading2"]), p(m.summary)] + bullets(m.learning_objectives)
    story.append(PageBreak())

    story.append(p("Lessons", styles["Heading1"]))
    for l in course.lessons.lessons:
        story += [p(f"Lesson {l.module_number}.{l.lesson_number}: {l.title}", styles["Heading2"])] + md_block(l.notes)
        if l.examples:
            story += [p("**Examples**")] + bullets(l.examples)
        if l.exercises:
            story += [p("**Exercises**")] + bullets(l.exercises)
        if l.case_study:
            story.append(p(f"**Case study:** {l.case_study}"))
        story.append(Spacer(1, 8))
    story.append(PageBreak())

    story.append(p("Assessments & Rubrics", styles["Heading1"]))
    for a in course.assessments.items:
        story += [p(f"{a.title} ({a.type.upper()})", styles["Heading2"]), p(a.prompt)]
        story += [p(f"{chr(65 + i)}. {o}") for i, o in enumerate(a.options)]
        story.append(p(f"**Answer:** {_answer_text(a)}"))
        story.append(p(f"**Mapped objective:** {a.learning_objective}"))
        if a.rubric:
            story.append(p(f"**Rubric:** {a.rubric}"))
        story.append(Spacer(1, 6))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


# ------------------------------------------------------------------------- ZIP
def build_course_zip(course: CoursePackage, markdown: str = None, pdf: bytes = None) -> bytes:
    """Pass pre-built `markdown`/`pdf` to avoid rendering them twice."""
    markdown = markdown if markdown is not None else build_markdown(course)
    pdf = pdf if pdf is not None else build_pdf(course)

    def dump(model):
        return json.dumps(model.model_dump(), indent=2, ensure_ascii=False)

    with io.BytesIO() as buf:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("Complete_Course.md", markdown)
            z.writestr("Complete_Course.pdf", pdf)
            z.writestr("Lessons.md", build_lessons_markdown(course))
            z.writestr("Answer_Key.md", build_answer_key_markdown(course))
            z.writestr("Curriculum.json", dump(course.curriculum))
            z.writestr("Assessments.json", dump(course.assessments))
            z.writestr("Validation_Report.json", dump(course.validation))
        return buf.getvalue()
