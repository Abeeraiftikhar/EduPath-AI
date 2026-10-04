from core.schemas import CourseRequest, CoursePackage
from core.llm_provider import GeminiProvider, ProviderError
from core.mock_provider import MockProvider
from core.config import settings
from core.utils import snap_objectives
from agents.curriculum_agent import CurriculumAgent
from agents.content_agent import ContentAgent
from agents.assessment_agent import AssessmentAgent
from agents.quality_agent import QualityAgent

AGENT_STEPS = ["Curriculum Architect", "Content Creator", "Assessment Agent", "Quality & Validation Agent"]


class CourseOrchestrator:
    """Runs the EduPath-AI pipeline and owns the validate -> targeted-regeneration loop."""

    def __init__(self, provider="mock", inject_fault=False):
        self.provider_name = provider
        self.provider = GeminiProvider() if provider == "gemini" else MockProvider(inject_fault=inject_fault)
        self.curriculum_agent = CurriculumAgent(self.provider)
        self.content_agent = ContentAgent(self.provider)
        self.assessment_agent = AssessmentAgent(self.provider)
        self.quality_agent = QualityAgent()

    def generate(self, topic, audience, duration, difficulty, learning_goal, on_step=None):
        """`on_step(agent_name, state, detail)` is called with state 'running' or 'done' for live progress."""
        step = on_step or (lambda *args: None)
        request = CourseRequest(
            topic=topic, audience=audience, duration=duration,
            difficulty=difficulty, learning_goal=learning_goal,
        )

        step(AGENT_STEPS[0], "running", "")
        curriculum = self.curriculum_agent.run(request)
        step(AGENT_STEPS[0], "done", f"{len(curriculum.modules)} modules")

        step(AGENT_STEPS[1], "running", "")
        lessons = self.content_agent.run(request, curriculum)
        step(AGENT_STEPS[1], "done", f"{len(lessons.lessons)} lessons")

        step(AGENT_STEPS[2], "running", "")
        assessments = self.assessment_agent.run(request, curriculum, lessons)
        snap_objectives(assessments.items, curriculum)
        step(AGENT_STEPS[2], "done", f"{len(assessments.items)} items")

        step(AGENT_STEPS[3], "running", "")
        validation = self.quality_agent.run(curriculum, lessons, assessments, duration)
        step(AGENT_STEPS[3], "done", f"{validation.status} ({validation.score:.0f}%)")

        # Feedback loop: send the validator's issues back to ONLY the failing components.
        resolved, attempts = [], 1
        while validation.status == "FAIL" and attempts <= settings.max_validation_retries:
            attempts += 1
            feedback = validation.issues
            failed = {c.component for c in validation.checks if not c.passed}
            step("Regeneration", "running", f"Attempt {attempts}: fixing {', '.join(sorted(failed))}")
            if "curriculum" in failed:       # everything downstream depends on it
                curriculum = self.curriculum_agent.run(request, feedback)
                failed |= {"lessons", "assessments"}
            if "lessons" in failed:
                lessons = self.content_agent.run(request, curriculum, feedback)
            if "assessments" in failed:
                assessments = self.assessment_agent.run(request, curriculum, lessons, feedback)
                snap_objectives(assessments.items, curriculum)
            resolved += [i for i in feedback if i not in resolved]
            validation = self.quality_agent.run(curriculum, lessons, assessments, duration)
            step("Regeneration", "done", f"{validation.status} ({validation.score:.0f}%)")

        validation.attempts = attempts
        validation.resolved_issues = [i for i in resolved if i not in validation.issues]
        return CoursePackage(
            request=request, curriculum=curriculum, lessons=lessons,
            assessments=assessments, validation=validation, provider_used=self.provider_name,
        )


def generate_course(provider, topic, audience, duration, difficulty, learning_goal,
                    on_step=None, inject_fault=False):
    """Safe entry point for the UI: if Gemini fails, fall back to demo output with a visible notice."""
    try:
        return CourseOrchestrator(provider, inject_fault).generate(
            topic, audience, duration, difficulty, learning_goal, on_step)
    except ProviderError as exc:
        if provider != "gemini":
            raise
        if on_step:
            on_step("Gemini", "done", "unavailable, switching to demo output")
        package = CourseOrchestrator("mock", inject_fault).generate(
            topic, audience, duration, difficulty, learning_goal, on_step)
        package.notice = f"Gemini unavailable ({exc}). Showing demo output instead."
        package.notice_details = exc.details
        return package
