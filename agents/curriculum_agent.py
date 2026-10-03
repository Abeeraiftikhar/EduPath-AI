from core.schemas import CourseRequest, Curriculum

class CurriculumAgent:
    def __init__(self, provider):
        self.provider = provider

    def run(self, request: CourseRequest) -> Curriculum:
        if hasattr(self.provider, "curriculum"):
            return self.provider.curriculum(request)
        prompt = f"""
You are the Curriculum Architect for EduPath-AI.
Create a coherent curriculum from this request:
{request.model_dump_json(indent=2)}
Requirements: prerequisites, measurable learning objectives, modules and a realistic roadmap.
Return only data matching the supplied Curriculum schema.
"""
        return self.provider.generate_structured(prompt, Curriculum)
