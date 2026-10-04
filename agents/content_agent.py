from agents.base import feedback_block
from core.schemas import CourseRequest, Curriculum, LessonPackage

class ContentAgent:
    def __init__(self, provider):
        self.provider = provider

    def run(self, request: CourseRequest, curriculum: Curriculum, feedback=None) -> LessonPackage:
        if hasattr(self.provider, "lessons"):
            return self.provider.lessons(request, curriculum, feedback)
        prompt = f"""
You are the Content Creator for EduPath-AI.
Generate lesson notes, examples, exercises and case studies aligned to every module.
Every lesson needs non-empty notes (Markdown), at least one example and at least one exercise. Lesson titles must be unique.
Request:
{request.model_dump_json(indent=2)}
Curriculum:
{curriculum.model_dump_json(indent=2)}
Return only LessonPackage schema data. Avoid inventing citations or unverifiable sources.
{feedback_block(feedback)}"""
        return self.provider.generate_structured(prompt, LessonPackage)
