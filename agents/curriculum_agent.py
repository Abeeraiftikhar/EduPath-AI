from agents.base import feedback_block
from core.schemas import CourseRequest, Curriculum

class CurriculumAgent:
    def __init__(self, provider):
        self.provider = provider

    def run(self, request: CourseRequest, feedback=None) -> Curriculum:
        if hasattr(self.provider, "curriculum"):
            return self.provider.curriculum(request, feedback)
        prompt = f"""
You are the Curriculum Architect for EduPath-AI.
Create a coherent curriculum from this request. The topic may be a single word or a short phrase (e.g. "Python"); treat it as the subject to teach, never ask for clarification:
{request.model_dump_json(indent=2)}
Requirements: prerequisites, measurable learning objectives, modules and a realistic roadmap.
Return only data matching the supplied Curriculum schema.
{feedback_block(feedback)}"""
        return self.provider.generate_structured(prompt, Curriculum)
