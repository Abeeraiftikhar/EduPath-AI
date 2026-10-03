from core.schemas import CourseRequest, Curriculum, LessonPackage, AssessmentPackage

class AssessmentAgent:
    def __init__(self, provider):
        self.provider = provider

    def run(self, request: CourseRequest, curriculum: Curriculum, lessons: LessonPackage) -> AssessmentPackage:
        if hasattr(self.provider, "assessments"):
            return self.provider.assessments(request, curriculum, lessons)
        prompt = f"""
You are the Assessment Agent for EduPath-AI.
Create MCQs, quizzes, assignments and/or a project mapped to learning objectives.
Every item needs an answer; longer tasks need a concise rubric.
Request:
{request.model_dump_json(indent=2)}
Curriculum:
{curriculum.model_dump_json(indent=2)}
Lessons:
{lessons.model_dump_json(indent=2)}
Return only AssessmentPackage schema data.
"""
        return self.provider.generate_structured(prompt, AssessmentPackage)
