from core.schemas import Curriculum, LessonPackage, AssessmentPackage, ValidationReport

class QualityAgent:
    def run(self, curriculum: Curriculum, lessons: LessonPackage, assessments: AssessmentPackage) -> ValidationReport:
        issues = []
        checked = []
        checked.append("Curriculum has modules and learning objectives.")
        if not curriculum.modules:
            issues.append("No curriculum modules generated.")
        if any(not m.learning_objectives for m in curriculum.modules):
            issues.append("One or more modules have no learning objectives.")

        checked.append("Every module has lesson content.")
        module_numbers = {m.number for m in curriculum.modules}
        lesson_modules = {l.module_number for l in lessons.lessons}
        missing_lessons = module_numbers - lesson_modules
        if missing_lessons:
            issues.append(f"Missing lessons for module(s): {sorted(missing_lessons)}")

        checked.append("Assessments contain answers and objective mappings.")
        if not assessments.items:
            issues.append("No assessment items generated.")
        for item in assessments.items:
            if not item.answer.strip():
                issues.append(f"Assessment '{item.title}' has no answer.")
            if not item.learning_objective.strip():
                issues.append(f"Assessment '{item.title}' is not mapped to a learning objective.")

        checked.append("Basic duplicate-title check.")
        titles = [l.title.strip().lower() for l in lessons.lessons]
        if len(titles) != len(set(titles)):
            issues.append("Duplicate lesson titles detected.")

        status = "PASS" if not issues else "FAIL"
        score = max(0.0, round(100 * (1 - len(issues) / max(1, len(checked) + 2)), 1))
        return ValidationReport(
            status=status,
            score=score,
            issues=issues,
            feedback=["Regenerate the relevant component when validation fails."] if issues else ["Package is structurally aligned and ready for export."],
            checked_items=checked,
        )
