from core.schemas import CourseRequest, CoursePackage
from core.llm_provider import GeminiProvider
from core.mock_provider import MockProvider
from core.config import settings
from agents.curriculum_agent import CurriculumAgent
from agents.content_agent import ContentAgent
from agents.assessment_agent import AssessmentAgent
from agents.quality_agent import QualityAgent

class CourseOrchestrator:
    """Runs the EduPath-AI pipeline and owns the validation/regeneration loop."""

    def __init__(self, provider="mock"):
        self.provider_name = provider
        self.provider = GeminiProvider() if provider == "gemini" else MockProvider()
        self.curriculum_agent = CurriculumAgent(self.provider)
        self.content_agent = ContentAgent(self.provider)
        self.assessment_agent = AssessmentAgent(self.provider)
        self.quality_agent = QualityAgent()

    def generate(self, topic, audience, duration, difficulty, learning_goal):
        request = CourseRequest(
            topic=topic, audience=audience, duration=duration,
            difficulty=difficulty, learning_goal=learning_goal
        )
        curriculum = self.curriculum_agent.run(request)
        lessons = self.content_agent.run(request, curriculum)
        assessments = self.assessment_agent.run(request, curriculum, lessons)
        validation = self.quality_agent.run(curriculum, lessons, assessments)

        # One controlled regeneration pass, matching the brief's feedback-loop concept.
        retries = settings.max_validation_retries
        attempt = 0
        while validation.status == "FAIL" and attempt < retries and self.provider_name == "gemini":
            attempt += 1
            lessons = self.content_agent.run(request, curriculum)
            assessments = self.assessment_agent.run(request, curriculum, lessons)
            validation = self.quality_agent.run(curriculum, lessons, assessments)

        return CoursePackage(
            request=request,
            curriculum=curriculum,
            lessons=lessons,
            assessments=assessments,
            validation=validation,
        )
