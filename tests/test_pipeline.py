import io
import zipfile

import pytest

from agents.quality_agent import QualityAgent
from core.exporter import build_course_zip, build_pdf
from core.llm_provider import GeminiProvider, ProviderError, friendly_error
from core.orchestrator import CourseOrchestrator, generate_course
from core.schemas import Curriculum, LessonPackage, AssessmentPackage
from core.config import settings
from core.mock_provider import MockProvider
from core.schemas import CourseRequest


def make(topic="Python for Bioinformatics", duration="4 Weeks", difficulty="Beginner", **kw):
    return CourseOrchestrator("mock", **kw).generate(
        topic=topic, audience="Undergraduate", duration=duration,
        difficulty=difficulty, learning_goal="Learn Python for biological sequence analysis.",
    )


def parts(result):
    """Deep copies of the generated parts, so a test can break them safely."""
    return (result.curriculum.model_copy(deep=True),
            result.lessons.model_copy(deep=True),
            result.assessments.model_copy(deep=True))


def failed(report):
    return {c.name for c in report.checks if not c.passed}


# ---------------------------------------------------------------- pipeline
def test_mock_pipeline_generates_complete_package():
    result = make()
    assert result.curriculum.modules and result.lessons.lessons and result.assessments.items
    assert result.validation.status == "PASS"
    assert result.validation.score == 100.0


def test_quality_mapping():
    result = make(topic="Scientific Writing", duration="2 Weeks", difficulty="Intermediate")
    objectives = {o for m in result.curriculum.modules for o in m.learning_objectives}
    assert all(a.learning_objective in objectives for a in result.assessments.items)


@pytest.mark.parametrize("duration,modules", [("1 Week", 2), ("2 Weeks", 3), ("4 Weeks", 4), ("6 Weeks", 5), ("12 Weeks", 6)])
def test_mock_output_scales_with_duration(duration, modules):
    result = make(duration=duration)
    assert len(result.curriculum.modules) == modules
    assert len(result.lessons.lessons) == 2 * modules
    assert len(result.curriculum.roadmap) == modules
    assert result.validation.status == "PASS"


def test_mock_output_reflects_topic_and_difficulty():
    easy, hard = make(topic="Astronomy", difficulty="Beginner"), make(topic="Astronomy", difficulty="Advanced")
    assert "Astronomy" in easy.curriculum.modules[0].title
    assert easy.curriculum.modules[0].learning_objectives != hard.curriculum.modules[0].learning_objectives


# ----------------------------------------------------------- quality agent
def test_quality_agent_detects_missing_answer_and_rubric_and_bad_mcq():
    curriculum, lessons, assessments = parts(make())
    assessments.items[0].answer = "Z"                     # invalid MCQ letter
    assessments.items[1].answer = ""                      # missing answer
    next(i for i in assessments.items if i.type == "project").rubric = None
    report = QualityAgent().run(curriculum, lessons, assessments, "4 Weeks")
    assert report.status == "FAIL"
    assert {"Multiple-choice answers are valid", "Assessments exist and include answers",
            "Assignments and projects have rubrics"} <= failed(report)
    assert all(c.component == "assessments" for c in report.checks if not c.passed)
    assert report.score < 100


def test_quality_agent_detects_unassessed_objective_and_unmapped_item():
    curriculum, lessons, assessments = parts(make())
    assessments.items = [i for i in assessments.items if i.learning_objective != curriculum.modules[0].learning_objectives[1]]
    assessments.items[0].learning_objective = "Something not in the curriculum"
    report = QualityAgent().run(curriculum, lessons, assessments, "4 Weeks")
    assert {"Every learning objective is assessed", "Assessments map to real learning objectives"} <= failed(report)


def test_quality_agent_detects_lesson_problems():
    curriculum, lessons, assessments = parts(make())
    lessons.lessons[0].exercises = []
    lessons.lessons[1].title = lessons.lessons[0].title
    lessons.lessons = [l for l in lessons.lessons if l.module_number != 2]
    report = QualityAgent().run(curriculum, lessons, assessments, "4 Weeks")
    assert {"Every module has lesson content", "Every lesson has notes, examples and exercises",
            "Lesson titles are unique"} <= failed(report)


def test_quality_agent_flags_unrealistic_module_count():
    curriculum, lessons, assessments = parts(make(duration="4 Weeks"))
    report = QualityAgent().run(curriculum, lessons, assessments, "12 Weeks")
    assert report.status == "PASS"                         # 4 modules is acceptable for 12 weeks
    report = QualityAgent().run(Curriculum(title="t", description="d", modules=[]), LessonPackage(lessons=[]),
                                AssessmentPackage(items=[]), "4 Weeks")
    assert report.status == "FAIL" and "Curriculum has modules with learning objectives" in failed(report)


# -------------------------------------------------------- feedback loop
def test_feedback_loop_recovers_from_injected_fault():
    steps = []
    result = CourseOrchestrator("mock", inject_fault=True).generate(
        "Python", "Students", "4 Weeks", "Beginner", "Learn Python.", on_step=lambda *a: steps.append(a))
    v = result.validation
    assert v.status == "PASS" and v.attempts == 2
    assert len(v.resolved_issues) == 3                     # empty exercises, bad MCQ answer, missing rubric
    assert any(s[0] == "Regeneration" for s in steps)


def test_fault_is_not_repeated_without_injection():
    assert make().validation.attempts == 1


def test_mock_provider_gives_clean_output_when_feedback_present():
    provider = MockProvider(inject_fault=True)
    req = CourseRequest(topic="T", audience="A", duration="2 Weeks", difficulty="Beginner", learning_goal="G")
    curriculum = provider.curriculum(req)
    assert provider.lessons(req, curriculum).lessons[0].exercises == []
    assert provider.lessons(req, curriculum, feedback=["fix"]).lessons[0].exercises


# ------------------------------------------------------------ exporter
def test_zip_contains_all_files_and_full_content():
    zf = zipfile.ZipFile(io.BytesIO(build_course_zip(make())))
    assert set(zf.namelist()) == {"Complete_Course.md", "Complete_Course.pdf", "Lessons.md", "Answer_Key.md",
                                  "Curriculum.json", "Assessments.json", "Validation_Report.json"}
    full = zf.read("Complete_Course.md").decode()
    assert "**Case study:**" in full and "**Rubric:**" in full and "A. " in full
    assert "Answer:" not in zf.read("Lessons.md").decode()      # Lessons.md is no longer a duplicate
    assert "Answer:" in zf.read("Answer_Key.md").decode()
    assert zf.read("Complete_Course.pdf").startswith(b"%PDF")


def test_pdf_handles_special_characters():
    result = CourseOrchestrator("mock").generate(
        'R&D <Chemistry> "Basics"', "Grads & <b>Staff</b>", "4 Weeks", "Advanced", "Goal with & and <tags> **bold**")
    assert build_pdf(result).startswith(b"%PDF")


# ------------------------------------------------------ Gemini handling
@pytest.fixture
def no_gemini_key():
    """Settings is a frozen dataclass, so swap the key via object.__setattr__ and restore it afterwards."""
    original = settings.gemini_api_key
    object.__setattr__(settings, "gemini_api_key", "")
    yield
    object.__setattr__(settings, "gemini_api_key", original)


def test_gemini_requires_key(no_gemini_key):
    with pytest.raises(ProviderError, match="GEMINI_API_KEY"):
        GeminiProvider()


def test_gemini_failure_falls_back_to_demo_with_notice(no_gemini_key):
    result = generate_course("gemini", "Topic", "Audience", "2 Weeks", "Beginner", "Goal")
    assert result.provider_used == "mock" and result.validation.status == "PASS"
    assert "Gemini unavailable" in result.notice


@pytest.mark.parametrize("raw,expected", [
    ("429 RESOURCE_EXHAUSTED quota", "quota"),
    ("403 PERMISSION_DENIED api key invalid", "API key"),
    ("Request timed out", "network"),
])
def test_friendly_errors(raw, expected):
    err = friendly_error(RuntimeError(raw))
    assert expected in str(err) and raw in err.details


def test_gemini_provider_retries_then_succeeds(monkeypatch):
    class FakeModels:
        calls = 0

        def generate_content(self, **kwargs):
            FakeModels.calls += 1
            if FakeModels.calls < 3:
                raise RuntimeError("503 unavailable")
            return type("R", (), {"parsed": None, "text": '{"lessons": []}'})()

    provider = GeminiProvider.__new__(GeminiProvider)
    provider.client = type("C", (), {"models": FakeModels()})()
    provider.models = ["fake", "fake-2"]
    monkeypatch.setattr("core.llm_provider.time.sleep", lambda s: None)
    assert provider.generate_structured("p", LessonPackage).lessons == []
    assert FakeModels.calls == 3


# ------------------------------------------------- topic handling & options
from core.options import AUDIENCES, LEARNING_GOALS, DURATIONS, DIFFICULTIES, SAMPLE  # noqa: E402
from core.utils import clean_topic, validate_topic, snap_objectives  # noqa: E402


@pytest.mark.parametrize("raw,expected", [
    ("python", "Python"),
    ("  digital   marketing ", "Digital Marketing"),
    ("python for bioinformatics", "Python for Bioinformatics"),
    ("SQL basics", "SQL Basics"),
])
def test_clean_topic(raw, expected):
    assert clean_topic(raw) == expected


def test_validate_topic():
    assert validate_topic("Python") is None                  # a single word is valid
    assert validate_topic("") and validate_topic("a") and validate_topic("123") and validate_topic("x" * 81)


@pytest.mark.parametrize("topic", ["python", "Photosynthesis", "SQL", "Python course"])
def test_single_word_topics_produce_valid_courses(topic):
    assert make(topic=clean_topic(topic)).validation.status == "PASS"


def test_every_form_option_generates_a_valid_course():
    for goal in LEARNING_GOALS:
        for audience in AUDIENCES:
            r = CourseOrchestrator("mock").generate("Python", audience, DURATIONS[0], DIFFICULTIES[2], goal)
            assert r.validation.status == "PASS"


def test_sample_profile_uses_valid_options():
    assert SAMPLE["audience"] in AUDIENCES and SAMPLE["goal"] in LEARNING_GOALS
    assert SAMPLE["duration"] in DURATIONS and SAMPLE["difficulty"] in DIFFICULTIES


def test_snap_objectives_repairs_paraphrased_mapping():
    curriculum, _, assessments = parts(make())
    original = assessments.items[0].learning_objective
    assessments.items[0].learning_objective = original.rstrip(".").lower() + " effectively"
    assert snap_objectives(assessments.items, curriculum) == 1
    assert assessments.items[0].learning_objective == original
    assessments.items[1].learning_objective = "Totally unrelated words"   # too different: left alone
    assert snap_objectives(assessments.items, curriculum) == 0


# ---------------------------------------------- coverage top-up (Gemini gaps)
class GappyLLM:
    """Stub LLM: its first assessment draft skips every second objective, as a real model sometimes does.
    A targeted request ('ONLY these learning objectives') returns just the missing items."""

    def __init__(self):
        self.mock, self.calls = MockProvider(), []
        self.req = CourseRequest(topic="Python", audience="Undergraduate students", duration="4 Weeks",
                                 difficulty="Beginner", learning_goal="Build practical, job-ready skills")

    def generate_structured(self, prompt, schema):
        self.calls.append("topup" if "ONLY for these learning objectives" in prompt else schema.__name__)
        curriculum = self.mock.curriculum(self.req)
        if schema.__name__ == "Curriculum":
            return curriculum
        if schema.__name__ == "LessonPackage":
            return self.mock.lessons(self.req, curriculum)
        full = self.mock.assessments(self.req, curriculum, None)
        if "ONLY for these learning objectives" in prompt:
            full.items = [i for i in full.items if i.learning_objective in prompt]
        else:
            full.items = [i for i in full.items if i.type != "quiz"]      # leaves objective B of each module unassessed
        return full


def test_missing_objective_coverage_is_fixed_by_targeted_topup():
    llm = GappyLLM()
    orch = CourseOrchestrator("mock")
    for agent in (orch.curriculum_agent, orch.content_agent, orch.assessment_agent):
        agent.provider = llm
    result = orch.generate("Python", "Undergraduate students", "4 Weeks", "Beginner", "Build practical, job-ready skills")
    assert result.validation.status == "PASS" and result.validation.attempts == 2
    assert llm.calls.count("topup") == 1 and llm.calls.count("AssessmentPackage") == 1   # no full regeneration
    assert any("no assessment" in i for i in result.validation.resolved_issues)
