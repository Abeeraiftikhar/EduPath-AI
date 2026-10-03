from core.orchestrator import CourseOrchestrator

def test_mock_pipeline_generates_complete_package():
    result = CourseOrchestrator("mock").generate(
        topic="Python for Bioinformatics",
        audience="Undergraduate",
        duration="4 Weeks",
        difficulty="Beginner",
        learning_goal="Learn Python for biological sequence analysis."
    )
    assert result.curriculum.modules
    assert result.lessons.lessons
    assert result.assessments.items
    assert result.validation.status == "PASS"

def test_quality_mapping():
    result = CourseOrchestrator("mock").generate(
        topic="Scientific Writing",
        audience="Researchers",
        duration="2 Weeks",
        difficulty="Intermediate",
        learning_goal="Write structured scientific content."
    )
    objectives = {o for m in result.curriculum.modules for o in m.learning_objectives}
    assert all(a.learning_objective in objectives for a in result.assessments.items)
