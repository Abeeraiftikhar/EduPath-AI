from agents.base import feedback_block
from core.schemas import CourseRequest, Curriculum, LessonPackage, AssessmentPackage

class AssessmentAgent:
    def __init__(self, provider):
        self.provider = provider

    def run(self, request: CourseRequest, curriculum: Curriculum, lessons: LessonPackage, feedback=None) -> AssessmentPackage:
        if hasattr(self.provider, "assessments"):
            return self.provider.assessments(request, curriculum, lessons, feedback)
        prompt = f"""
You are the Assessment Agent for EduPath-AI.
Create MCQs, quizzes, assignments and/or a project mapped to learning objectives.
Rules (they are machine-checked):
- Every learning objective in the curriculum must be assessed by at least one item.
- learning_objective must be copied EXACTLY from a curriculum objective.
- Every item needs an answer. For type "mcq", give 4 options and set answer to the correct letter (A-D).
- Items of type "assignment" and "project" must include a concise rubric.
Request:
{request.model_dump_json(indent=2)}
Curriculum:
{curriculum.model_dump_json(indent=2)}
Lessons:
{lessons.model_dump_json(indent=2)}
Return only AssessmentPackage schema data.
{feedback_block(feedback)}"""
        return self.provider.generate_structured(prompt, AssessmentPackage)
