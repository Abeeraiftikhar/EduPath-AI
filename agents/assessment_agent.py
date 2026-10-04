from agents.base import feedback_block
from core.schemas import CourseRequest, Curriculum, LessonPackage, AssessmentPackage

class AssessmentAgent:
    def __init__(self, provider):
        self.provider = provider

    def run(self, request: CourseRequest, curriculum: Curriculum, lessons: LessonPackage, feedback=None) -> AssessmentPackage:
        if hasattr(self.provider, "assessments"):
            return self.provider.assessments(request, curriculum, lessons, feedback)
        objective_count = sum(len(m.learning_objectives) for m in curriculum.modules)
        prompt = f"""
You are the Assessment Agent for EduPath-AI.
Create MCQs, quizzes, assignments and/or a project mapped to learning objectives.
Rules (they are machine-checked):
- The curriculum has {objective_count} learning objectives. Return AT LEAST {objective_count} items so that every objective is assessed by at least one item.
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


    def complete(self, request: CourseRequest, curriculum: Curriculum, missing: list):
        """Create items ONLY for objectives that no existing item covers. Returns None for providers
        that cannot do a targeted call (the mock provider always produces full coverage)."""
        if hasattr(self.provider, "assessments"):
            return None
        listed = "\n".join(f"- {o}" for o in missing)
        prompt = f"""
You are the Assessment Agent for EduPath-AI.
A draft assessment set is missing coverage. Create assessment items ONLY for these learning objectives,
at least one item per objective, and copy each objective text EXACTLY into learning_objective:
{listed}
Rules: every item needs an answer; for type "mcq" give 4 options and set answer to the correct letter (A-D);
items of type "assignment" and "project" need a concise rubric.
Course: {request.topic} for {request.audience} ({request.difficulty}).
Return only AssessmentPackage schema data.
"""
        return self.provider.generate_structured(prompt, AssessmentPackage)
