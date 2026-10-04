from core.schemas import (
    CourseRequest, Curriculum, LessonPackage, AssessmentPackage,
    Module, Lesson, AssessmentItem,
)
from core.utils import parse_weeks

# Verbs get stronger with difficulty (Bloom-style), so Beginner and Advanced courses read differently.
VERBS = {
    "Beginner": ("Describe", "Identify", "Apply"),
    "Intermediate": ("Explain", "Apply", "Analyze"),
    "Advanced": ("Analyze", "Design", "Critically evaluate"),
}

# role -> (title template, summary, ((verb index, objective phrase), (verb index, objective phrase)))
BLUEPRINTS = {
    "foundations": ("Foundations of {t}", "Build the conceptual foundation and shared vocabulary.",
                    ((0, "the core concepts of {t}"), (1, "the essential terminology and tools of {t}"))),
    "core": ("Core Concepts and Tools", "Work with the main techniques through guided examples.",
             ((0, "the standard workflow used in {t}"), (1, "which tool or method suits a given {t} problem"))),
    "practice": ("{t} in Practice", "Apply the workflow to realistic, hands-on scenarios.",
                 ((2, "the workflow to a realistic {t} scenario"), (1, "errors and unexpected results in {t} work"))),
    "advanced": ("Advanced Applications", "Extend the skills to harder, less structured problems.",
                 ((2, "advanced {t} techniques to open-ended problems"), (0, "trade-offs between alternative {t} approaches"))),
    "capstone": ("Applied Project", "Integrate everything in a realistic mini-project.",
                 ((1, "a complete {t} solution for a defined goal"), (2, "the solution against clear success criteria"))),
}

ROLES_BY_COUNT = {
    2: ["foundations", "capstone"],
    3: ["foundations", "practice", "capstone"],
    4: ["foundations", "core", "practice", "capstone"],
    5: ["foundations", "core", "practice", "advanced", "capstone"],
    6: ["foundations", "core", "practice", "advanced", "practice", "capstone"],
}


def module_count(weeks: int) -> int:
    return 2 if weeks <= 1 else 3 if weeks == 2 else 4 if weeks <= 4 else 5 if weeks <= 6 else 6


def _goal(req) -> str:
    return req.learning_goal.strip().rstrip(".")


def _audience(req) -> str:
    """Lower-case a generic audience ('Undergraduate students') but keep names like 'PhD researchers'."""
    a = req.audience
    return a if any(c.isupper() for c in a[1:]) else a.lower()


def _article(word: str) -> str:
    return "An" if word[:1].lower() in "aeiou" else "A"


class MockProvider:
    """Deterministic provider for demos and tests: no API key, but it adapts to the request.

    `inject_fault=True` makes the first attempt deliberately flawed so the validate ->
    regenerate loop can be demonstrated. Any `feedback` from the validator produces a clean result.
    """

    def __init__(self, inject_fault: bool = False):
        self.inject_fault = inject_fault

    def _faulty(self, feedback) -> bool:
        return self.inject_fault and not feedback

    # ---------------------------------------------------------------- curriculum
    def curriculum(self, req: CourseRequest, feedback=None) -> Curriculum:
        weeks = parse_weeks(req.duration)
        verbs = VERBS.get(req.difficulty, VERBS["Intermediate"])
        roles = ROLES_BY_COUNT[module_count(weeks)]
        t = req.topic
        modules, used_titles = [], set()
        for number, role in enumerate(roles, start=1):
            title_tpl, summary, objs = BLUEPRINTS[role]
            title = title_tpl.format(t=t)
            if title in used_titles:
                title = f"{title} II"
            used_titles.add(title)
            modules.append(Module(
                number=number, title=title, summary=summary,
                prerequisites=[modules[-1].title] if modules else [],
                learning_objectives=[f"{verbs[v]} {phrase.format(t=t)}." for v, phrase in objs],
            ))
        return Curriculum(
            title=f"{t}: {req.duration} {req.difficulty} Learning Path",
            description=(f"{_article(req.difficulty)} {req.difficulty.lower()}, {parse_weeks(req.duration)}-week course for {_audience(req)}. "
                         f"Goal: {_goal(req).lower()}."
                         + (f" Designed for about {req.weekly_hours}." if req.weekly_hours else "")),
            prerequisites=["Basic computer literacy", f"Motivation to learn {t}"]
            + (["Some prior exposure to the subject area"] if req.difficulty != "Beginner" else []),
            modules=modules,
            roadmap=self._roadmap(modules, weeks),
        )

    @staticmethod
    def _roadmap(modules, weeks):
        n = len(modules)
        unit, total = ("Week", weeks) if weeks >= n else ("Day", weeks * 5)
        roadmap, start = [], 1
        for i, m in enumerate(modules):
            end = start + total // n + (1 if i < total % n else 0) - 1
            span = f"{unit} {start}" if start == end else f"{unit}s {start}-{end}"
            roadmap.append(f"{span}: {m.title}")
            start = end + 1
        return roadmap

    # ------------------------------------------------------------------- lessons
    def lessons(self, req: CourseRequest, curriculum: Curriculum, feedback=None) -> LessonPackage:
        lessons = []
        for m in curriculum.modules:
            for n, (kind, focus) in enumerate(
                [("Concepts", "explains the key ideas"), ("Guided Practice", "walks through a hands-on workflow")], start=1
            ):
                objectives = "\n".join(f"- {o}" for o in m.learning_objectives)
                lessons.append(Lesson(
                    module_number=m.number, lesson_number=n,
                    title=f"{m.title}: {kind}",
                    notes=(f"### {m.title}: {kind}\n\nThis lesson {focus} behind **{req.topic}** for "
                           f"{_audience(req)}.\n\n**By the end you will be able to:**\n{objectives}\n\n"
                           f"**Key idea:** {m.summary}"),
                    examples=[f"Worked example: {m.title.lower()} applied to a typical {req.topic} task.",
                              f"Interpretation example: reading the result of a {req.topic} activity for a learner in this audience."],
                    exercises=[f"Practice task: complete one {kind.lower()} activity on {req.topic}.",
                               "Reflect: explain your result in 3-5 sentences."],
                    case_study=(f"A learner's aim is to {_goal(req).lower()}. "
                                f"Decide how '{m.title}' contributes and justify each step."),
                    learning_objectives=m.learning_objectives,
                ))
        if self._faulty(feedback):
            lessons[0].exercises = []          # demo fault: caught by the quality agent
        return LessonPackage(lessons=lessons)

    # --------------------------------------------------------------- assessments
    def assessments(self, req: CourseRequest, curriculum: Curriculum, lessons: LessonPackage,
                    feedback=None) -> AssessmentPackage:
        t, items = req.topic, []
        for m in curriculum.modules:
            obj_a, obj_b = m.learning_objectives[0], m.learning_objectives[1]
            correct = (m.number - 1) % 4          # rotate the correct letter so answers are not always A
            distractors = iter([
                "By memorising terms without ever using them.",
                "By avoiding practical application altogether.",
                "By skipping any evaluation of the results.",
            ])
            options = [f"By applying it to a realistic {t} task and checking the result."
                       if i == correct else next(distractors) for i in range(4)]
            items.append(AssessmentItem(
                type="mcq", title=f"Module {m.number} Concept Check",
                prompt=f"Which option best shows a learner achieving this objective: \"{obj_a}\"",
                options=options, answer=chr(65 + correct), learning_objective=obj_a,
            ))
            items.append(AssessmentItem(
                type="quiz", title=f"Module {m.number} Short Quiz",
                prompt=f"In 2-3 sentences, show how you would meet this objective: \"{obj_b}\"",
                answer=f"A strong answer names the key {t} concept from '{m.title}' and gives one concrete example.",
                learning_objective=obj_b,
            ))
        mid, last = curriculum.modules[len(curriculum.modules) // 2], curriculum.modules[-1]
        items.append(AssessmentItem(
            type="assignment", title="Applied Task",
            prompt=f"Complete a small task showing practical use of {t}. Document your approach, result and one limitation.",
            answer="Instructor evaluates the submitted work against the rubric.",
            learning_objective=mid.learning_objectives[0],
            rubric="4 - accurate, complete and well justified; 3 - mostly correct; 2 - partial; 1 - insufficient evidence.",
        ))
        items.append(AssessmentItem(
            type="project", title="Capstone Mini-Project",
            prompt=f"Design a mini-project for the goal \"{_goal(req)}\". Include objective, method, output and evaluation.",
            answer="Project-specific; evaluate against objective, method, evidence and reflection.",
            learning_objective=last.learning_objectives[1],
            rubric="4 - strong alignment and evidence; 3 - adequate alignment; 2 - major gaps; 1 - incomplete.",
        ))
        if self._faulty(feedback):
            items[0].answer = "Z"                   # demo fault: invalid MCQ answer
            items[-2].rubric = None                 # demo fault: assignment without rubric
        return AssessmentPackage(items=items)
