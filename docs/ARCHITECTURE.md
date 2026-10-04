# EduPath-AI Architecture

## Pipeline

User input is validated into `CourseRequest`. `generate_course()` (the UI's safe entry point) wraps
`CourseOrchestrator`, which runs:

1. **Curriculum Architect** - modules, objectives, prerequisites, roadmap
2. **Content Creator** - lesson notes, examples, exercises, case studies
3. **Assessment Agent** - MCQs, quizzes, assignments, project, answer keys, rubrics
4. **Quality & Validation Agent** - rule-based checks (below)

The orchestrator reports each step through an `on_step(agent, state, detail)` callback, which the UI
renders as live progress.

## Quality checks (10)

| Check | Regenerates |
|---|---|
| Modules exist and each has learning objectives | curriculum |
| Module count fits the course duration | curriculum |
| Every module has lessons | lessons |
| Every lesson has notes, examples and exercises | lessons |
| Lesson titles are unique | lessons |
| Assessments exist and include answers | assessments |
| Assessments map to real learning objectives | assessments |
| Every learning objective is assessed | assessments |
| MCQ answers are valid (letter within the options) | assessments |
| Assignments and projects have rubrics | assessments |

`score = passed checks / total checks`. Each failed check carries a human-readable `detail`.

## Feedback loop

```text
generate -> validate -- PASS --> export
                |
              FAIL: issues become "Fix these problems" feedback
                    -> regenerate ONLY the failing component(s)
                       (curriculum failure also regenerates lessons + assessments)
                    -> validate again (up to MAX_VALIDATION_RETRIES, default 1)
```

The loop runs for every provider. `ValidationReport.attempts` and `resolved_issues` record what was fixed.
The "Demonstrate self-correction" option in demo mode injects deliberate faults on the first attempt so
the loop can be shown live.

## Reliability

- `GeminiProvider` retries up to 3 times with backoff and translates SDK errors into friendly
  `ProviderError` messages (quota, bad key, network, malformed JSON).
- If Gemini fails, `generate_course()` falls back to demo output and sets `CoursePackage.notice`.
- The UI never shows a raw stack trace; technical details sit in an expander.

## Separation of concerns

- `agents/` - agent responsibilities (`base.py` builds the feedback prompt section).
- `core/schemas.py` - structured contracts (Pydantic).
- `core/llm_provider.py` - isolates Gemini, retries and error translation.
- `core/mock_provider.py` - deterministic, input-aware provider that needs no external services.
- `core/orchestrator.py` - pipeline, progress callbacks, feedback loop, fallback.
- `core/exporter.py` - Markdown, PDF and ZIP builders (built once per course and cached in the session).
- `core/utils.py` - duration parsing and MCQ answer helpers.
- `app.py` - presentation layer.

## Interface layer (`app.py`, `ui/`, `assets/`)

- **Design system:** tokens (colour, radius, shadow, motion easing) live in `assets/theme.css`; `assets/theme_dark.css`
  only overrides the tokens, so every component themes automatically. Dark is the default.
- **Icons:** `st.html` strips inline `<svg>`, so Lucide-style icons are generated as CSS masks
  (`python ui/make_icons.py` writes `assets/icons.css`; use `<i class="ic ic-route"></i>`).
- **Static sections** are pure functions in `ui/sections.py` (all user text is escaped) and are unit-tested.
- **Wizard state:** answers live in `st.session_state.wiz`; widgets of other steps are unmounted, so values are
  copied on every Back/Continue (`save_wizard`). Generation is triggered via `pending`, run inline with a live
  progress card, then results are cached with their export files.
- **Motion:** CSS only. Scroll reveals use `animation-timeline: view()` (Chromium; other browsers simply show the
  content). Everything respects `prefers-reduced-motion`.
