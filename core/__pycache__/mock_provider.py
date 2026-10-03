from core.schemas import CourseRequest, Curriculum, LessonPackage, AssessmentPackage, Module, Lesson, AssessmentItem

class MockProvider:
    """Deterministic provider for UI development, testing and demos without an API key."""

    def curriculum(self, req: CourseRequest) -> Curriculum:
        return Curriculum(
            title=f"{req.topic}: {req.duration} Learning Path",
            description=f"A {req.difficulty.lower()} course for {req.audience}, focused on {req.learning_goal}",
            prerequisites=["Basic computer literacy"],
            modules=[
                Module(
                    number=1,
                    title="Foundations",
                    summary="Build the conceptual foundation.",
                    prerequisites=[],
                    learning_objectives=["Explain the core concepts of the topic.", "Identify essential terminology."],
                ),
                Module(
                    number=2,
                    title="Core Practice",
                    summary="Apply concepts through guided examples.",
                    prerequisites=["Foundations"],
                    learning_objectives=["Apply the main workflow.", "Interpret practical results."],
                ),
                Module(
                    number=3,
                    title="Applied Project",
                    summary="Integrate skills in a realistic mini-project.",
                    prerequisites=["Core Practice"],
                    learning_objectives=["Design a small solution.", "Evaluate the solution against a defined goal."],
                ),
            ],
            roadmap=["Week 1: Foundations", "Week 2: Core Practice", "Final phase: Applied Project"],
        )

    def lessons(self, req: CourseRequest, curriculum: Curriculum) -> LessonPackage:
        lessons = []
        for m in curriculum.modules:
            lessons.append(Lesson(
                module_number=m.number,
                lesson_number=1,
                title=f"{m.title}: Guided Lesson",
                notes=f"### {m.title}\n\nThis lesson introduces **{req.topic}** through a structured explanation, worked examples and guided practice. Connect each activity to the stated learning objectives.",
                examples=[f"Worked example related to {req.topic}", "Interpretation example using a realistic learner scenario."],
                exercises=[f"Practice task: apply the concept of {req.topic}.", "Explain your result in 3–5 sentences."],
                case_study=f"A learner needs to achieve this goal: {req.learning_goal}. Identify an appropriate workflow and justify each major step.",
                learning_objectives=m.learning_objectives,
            ))
        return LessonPackage(lessons=lessons)

    def assessments(self, req: CourseRequest, curriculum: Curriculum, lessons: LessonPackage) -> AssessmentPackage:
        items = [
            AssessmentItem(
                type="mcq", title="Concept Check",
                prompt=f"Which statement best describes the purpose of learning {req.topic} in this course?",
                options=[
                    f"To build skills aligned with: {req.learning_goal}",
                    "To memorize unrelated terminology",
                    "To skip practical application",
                    "To avoid evaluating results",
                ],
                answer="A", learning_objective=curriculum.modules[0].learning_objectives[0]
            ),
            AssessmentItem(
                type="assignment", title="Applied Task",
                prompt=f"Complete a small task demonstrating practical use of {req.topic}. Document your approach, result and one limitation.",
                answer="Instructor evaluates the submitted work against the rubric.",
                learning_objective=curriculum.modules[1].learning_objectives[0],
                rubric="4 — accurate, complete and well justified; 3 — mostly correct; 2 — partial; 1 — insufficient evidence."
            ),
            AssessmentItem(
                type="project", title="Capstone Mini-Project",
                prompt=f"Design a mini-project that addresses the learning goal: {req.learning_goal}. Include objective, method, output and evaluation.",
                answer="Project-specific; evaluate against objective, method, evidence and reflection.",
                learning_objective=curriculum.modules[2].learning_objectives[0],
                rubric="4 — strong alignment and evidence; 3 — adequate alignment; 2 — major gaps; 1 — incomplete."
            ),
        ]
        return AssessmentPackage(items=items)