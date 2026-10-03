import io
import json
import zipfile
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from core.schemas import CoursePackage

def _markdown(course: CoursePackage) -> str:
    lines = [f"# {course.curriculum.title}", "", course.curriculum.description, "",
             "## Request", ""]
    for k, v in course.request.model_dump().items():
        lines.append(f"- **{k.replace('_',' ').title()}:** {v}")
    lines += ["", "## Curriculum", ""]
    for m in course.curriculum.modules:
        lines += [f"### Module {m.number}: {m.title}", m.summary, "",
                  "**Learning objectives:**"]
        lines += [f"- {x}" for x in m.learning_objectives]
        lines.append("")
    lines += ["## Lessons", ""]
    for l in course.lessons.lessons:
        lines += [f"### Lesson {l.module_number}.{l.lesson_number}: {l.title}", l.notes, "",
                  "**Exercises:**"]
        lines += [f"- {x}" for x in l.exercises]
        lines.append("")
    lines += ["## Assessments", ""]
    for a in course.assessments.items:
        lines += [f"### {a.type.upper()}: {a.title}", a.prompt, f"**Answer:** {a.answer}",
                  f"**Mapped objective:** {a.learning_objective}", ""]
    lines += ["## Validation", "", f"**Status:** {course.validation.status}",
              f"**Score:** {course.validation.score}"]
    if course.validation.issues:
        lines += [f"- {x}" for x in course.validation.issues]
    return "\n".join(lines)

def _pdf(course: CoursePackage) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=.65*inch, leftMargin=.65*inch,
                            topMargin=.65*inch, bottomMargin=.65*inch)
    styles = getSampleStyleSheet()
    styles["Title"].alignment = TA_CENTER
    story = [Paragraph(course.curriculum.title, styles["Title"]),
             Spacer(1, 12), Paragraph(course.curriculum.description, styles["BodyText"]), Spacer(1, 16)]
    story.append(Paragraph("Curriculum", styles["Heading1"]))
    for m in course.curriculum.modules:
        story.append(Paragraph(f"Module {m.number}: {m.title}", styles["Heading2"]))
        story.append(Paragraph(m.summary, styles["BodyText"]))
        for obj in m.learning_objectives:
            story.append(Paragraph("• " + obj, styles["BodyText"]))
    story.append(PageBreak())
    story.append(Paragraph("Lessons", styles["Heading1"]))
    for l in course.lessons.lessons:
        story.append(Paragraph(l.title, styles["Heading2"]))
        story.append(Paragraph(l.notes.replace("\n", "<br/>"), styles["BodyText"]))
        for ex in l.exercises:
            story.append(Paragraph("• " + ex, styles["BodyText"]))
        story.append(Spacer(1, 8))
    story.append(PageBreak())
    story.append(Paragraph("Assessments & Rubrics", styles["Heading1"]))
    for a in course.assessments.items:
        story.append(Paragraph(a.title, styles["Heading2"]))
        story.append(Paragraph(a.prompt, styles["BodyText"]))
        story.append(Paragraph("Answer: " + a.answer, styles["BodyText"]))
        if a.rubric:
            story.append(Paragraph("Rubric: " + a.rubric, styles["BodyText"]))
    doc.build(story)
    return buf.getvalue()

def build_course_zip(course: CoursePackage) -> bytes:
    md = _markdown(course).encode("utf-8")
    pdf = _pdf(course)
    curriculum_json = json.dumps(course.curriculum.model_dump(), indent=2).encode("utf-8")
    assessments_json = json.dumps(course.assessments.model_dump(), indent=2).encode("utf-8")
    validation_json = json.dumps(course.validation.model_dump(), indent=2).encode("utf-8")
    with io.BytesIO() as buf:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("Complete_Course.md", md)
            z.writestr("Complete_Course.pdf", pdf)
            z.writestr("Curriculum.json", curriculum_json)
            z.writestr("Assessments.json", assessments_json)
            z.writestr("Validation_Report.json", validation_json)
            z.writestr("Lessons.md", md)
        return buf.getvalue()
