from core.schemas import (
    Curriculum, LessonPackage, AssessmentPackage, ValidationReport, ValidationCheck,
)
from core.utils import parse_weeks, mcq_answer_index


class QualityAgent:
    """Rule-based validator. Each check names the component to regenerate when it fails."""

    def run(self, curriculum: Curriculum, lessons: LessonPackage, assessments: AssessmentPackage,
            duration: str = "") -> ValidationReport:
        checks = []

        def add(name, passed, detail_if_failed, component):
            checks.append(ValidationCheck(
                name=name, passed=passed, component=component,
                detail="" if passed else detail_if_failed,
            ))

        # --- Curriculum -------------------------------------------------
        no_objectives = [m.number for m in curriculum.modules if not m.learning_objectives]
        add("Curriculum has modules with learning objectives",
            bool(curriculum.modules) and not no_objectives,
            "No modules generated." if not curriculum.modules
            else f"Module(s) {no_objectives} have no learning objectives.",
            "curriculum")

        if duration:
            weeks = parse_weeks(duration)
            low, high = (1, 4) if weeks <= 1 else (2, max(4, weeks * 2))
            count = len(curriculum.modules)
            add("Module count fits the course duration", low <= count <= high,
                f"{count} modules is unrealistic for {duration} (expected {low}-{high}).", "curriculum")

        # --- Lessons ----------------------------------------------------
        missing = sorted({m.number for m in curriculum.modules} - {l.module_number for l in lessons.lessons})
        add("Every module has lesson content", not missing,
            f"Missing lessons for module(s): {missing}.", "lessons")

        thin = [f"{l.module_number}.{l.lesson_number}" for l in lessons.lessons
                if not l.examples or not l.exercises or not l.notes.strip()]
        add("Every lesson has notes, examples and exercises", not thin,
            f"Lesson(s) {thin} lack notes, examples or exercises.", "lessons")

        titles = [l.title.strip().lower() for l in lessons.lessons]
        add("Lesson titles are unique", len(titles) == len(set(titles)),
            "Duplicate lesson titles detected.", "lessons")

        # --- Assessments ------------------------------------------------
        items = assessments.items
        no_answer = [i.title for i in items if not i.answer.strip()]
        add("Assessments exist and include answers", bool(items) and not no_answer,
            "No assessment items generated." if not items
            else f"Assessment(s) without an answer: {no_answer}.", "assessments")

        objectives = {o for m in curriculum.modules for o in m.learning_objectives}
        unmapped = [i.title for i in items if i.learning_objective not in objectives]
        add("Assessments map to real learning objectives", not unmapped,
            f"Assessment(s) not mapped to a curriculum objective: {unmapped}.", "assessments")

        uncovered = sorted(objectives - {i.learning_objective for i in items})
        add("Every learning objective is assessed", not uncovered,
            f"{len(uncovered)} objective(s) have no assessment, e.g. '{uncovered[0]}'." if uncovered else "",
            "assessments")

        bad_mcq = [i.title for i in items if i.type == "mcq" and mcq_answer_index(i.answer, i.options) < 0]
        add("Multiple-choice answers are valid", not bad_mcq,
            f"MCQ(s) with an invalid answer or options: {bad_mcq}.", "assessments")

        no_rubric = [i.title for i in items if i.type in ("assignment", "project") and not (i.rubric or "").strip()]
        add("Assignments and projects have rubrics", not no_rubric,
            f"Missing rubric for: {no_rubric}.", "assessments")

        passed = sum(c.passed for c in checks)
        issues = [c.detail for c in checks if not c.passed]
        return ValidationReport(
            status="PASS" if not issues else "FAIL",
            score=round(100 * passed / len(checks), 1),
            issues=issues,
            feedback=issues if issues else ["Package is structurally aligned and ready for export."],
            checked_items=[c.name for c in checks],
            checks=checks,
        )
