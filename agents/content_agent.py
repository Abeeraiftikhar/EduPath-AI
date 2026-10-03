from core.schemas import CourseRequest, Curriculum, LessonPackage

class ContentAgent:
    def __init__(self, provider):
        self.provider = provider

    def run(self, request: CourseRequest, curriculum: Curriculum) -> LessonPackage:
        if hasattr(self.provider, "lessons"):
            return self.provider.lessons(request, curriculum)
        prompt = f"""
You are the Content Creator for EduPath-AI.
Generate lesson notes, examples, exercises and case studies aligned to every module.
Request:
{request.model_dump_json(indent=2)}
Curriculum:
{curriculum.model_dump_json(indent=2)}
Return only LessonPackage schema data. Avoid inventing citations or unverifiable sources.
"""
        return self.provider.generate_structured(prompt, LessonPackage)
