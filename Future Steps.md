# Future Steps — Making EduPath-AI Excellent

Work is tracked on the **`waleed-works`** branch. Each step below is marked ✅ Done (with a short explanation of what was built and verified) or 🔲 Remaining (manual actions that need the owner).

**Progress: 9 of 10 steps fully done, plus the bonus round. Step 10 is done except for 3 manual items (deploy, screenshots, rehearsal). Gemini mode has now been tested live.**

## Status at a glance

| # | Step | Status |
|---|---|---|
| 1 | Mock mode responds to user input | ✅ Done |
| 2 | Meaningful Quality agent | ✅ Done |
| 3 | Real feedback loop | ✅ Done |
| 4 | Harden Gemini mode | ✅ Done |
| 5 | Fix and enrich exports | ✅ Done |
| 6 | Live progress while generating | ✅ Done |
| 7 | Upgraded results workspace | ✅ Done |
| 8 | Clean repo and dependencies | ✅ Done |
| 9 | Expanded tests | ✅ Done (23 passing) |
| 10 | Docs, deployment, demo polish | 🟡 Docs and sample done; 3 manual items left |

---

## ✅ Step 1 — Mock mode responds to the user's input
**What was done** (`core/mock_provider.py`, `core/utils.py`)
- The module count now follows the duration: 1 week → 2 modules, 2 → 3, 3–4 → 4, 5–6 → 5, 7+ → 6.
- The roadmap is split across the real duration (e.g. "Weeks 1-2: …", or "Days 1-3: …" for a 1-week course).
- Learning-objective verbs get stronger with difficulty (Beginner "Describe/Identify" → Advanced "Analyze/Design/Critically evaluate").
- The topic, audience and goal appear in module titles, lessons, case studies and questions.
- 2 lessons per module, 1 MCQ plus 1 short quiz per module, then an assignment and a capstone project. The correct MCQ letter rotates instead of always being "A".

**Verified:** parametrized tests for 1, 2, 4, 6 and 12 weeks, plus a topic/difficulty test.

## ✅ Step 2 — Make the Quality agent meaningful
**What was done** (`agents/quality_agent.py`, `core/schemas.py`)
- 10 explainable checks: module objectives, module count vs duration, lesson coverage, lesson completeness (notes/examples/exercises), unique titles, answers present, objective mapping, every objective assessed, valid MCQ answers, rubrics for assignments and projects.
- New `ValidationCheck(name, passed, detail, component)` model. Score is now `passed / total × 100` (the old formula was arbitrary).
- Each failed check names the component to regenerate, which Step 3 uses.

**Verified:** four tests, each breaking one aspect of a valid package and asserting the right check fails.

## ✅ Step 3 — Make the feedback loop real
**What was done** (`core/orchestrator.py`, `agents/base.py`, agents, mock provider)
- Validator issues are passed back to the agents as a "Fix these problems" prompt section.
- Only the failing component is regenerated. A curriculum failure also regenerates lessons and assessments, because they depend on it.
- The loop now runs for all providers (previously Gemini only) and records `attempts` and `resolved_issues`.
- The mock provider has an `inject_fault` mode. The UI exposes it as **"Demonstrate self-correction"**, so the loop can be shown live: FAIL (70%) → regeneration → PASS (100%).

**Verified:** `test_feedback_loop_recovers_from_injected_fault` (2 attempts, 3 issues resolved).

## ✅ Step 4 — Harden Gemini mode
**What was done** (`core/llm_provider.py`, `core/orchestrator.py`, `app.py`)
- `GeminiProvider` retries up to 3 times with exponential backoff, covering transient errors and malformed JSON.
- New `ProviderError` with friendly messages for quota/rate limit, bad key, network/timeout and schema mismatch. The raw cause goes into a "Technical details" expander.
- `generate_course()` falls back to demo output with a visible warning if Gemini fails or no key is set. The form shows whether a key is detected.
- The UI has a last-resort handler, so users never see a stack trace.

**Verified:** retry-then-succeed test with a fake client, fallback test, error-translation tests. Also checked end-to-end in the UI without a key.

## ✅ Step 5 — Fix and enrich the exports
**What was done** (`core/exporter.py`)
- Markdown and PDF now include prerequisites, roadmap, examples, exercises, case studies, MCQ options, answers and rubrics.
- The PDF renders Markdown properly (headings, bullets, bold) instead of showing raw `###`/`**`, escapes special characters (`& < >` no longer crash ReportLab), and has a cover block and page numbers.
- `Lessons.md` now contains only lessons (it was a duplicate), and there is a new `Answer_Key.md`. MCQ answers show the letter and the option text.
- The ZIP is built once per generated course and cached in the session instead of on every Streamlit rerun. PDF and Markdown also have their own download buttons.

**Verified:** ZIP-contents test and a PDF test with `R&D <Chemistry> "Basics"` plus HTML-like input.

## ✅ Step 6 — Show real progress while generating
**What was done** (`core/orchestrator.py`, `app.py`)
- `generate(..., on_step)` reports each agent as running/done with a detail ("4 modules", "FAIL (70%)", "Attempt 2: fixing …").
- The UI streams these into the `st.status` box, and the box collapses on completion.
- After generation the page smooth-scrolls to the "Course workspace" (best-effort, cosmetic).

## ✅ Step 7 — Upgrade the results workspace
**What was done** (`app.py`)
- **Validation tab:** a ✓/✗ checklist with failure details, a score pill ("PASS · 100% — 10/10 checks passed"), the self-correction history, and raw JSON in a collapsed expander.
- **Curriculum tab:** prerequisites list and a visual roadmap timeline.
- **Lessons tab:** case-study callout. **Assessments tab:** MCQ options with the correct one highlighted.
- Validation metric shows status plus score. A **New course** button resets the workspace. PDF and Markdown downloads sit beside the ZIP.
- Everything reuses the existing design tokens and card styles.

**Verified:** driven through Streamlit's `AppTest` (navigation, empty-form error, generate, Gemini fallback, reset) with no exceptions.

## ✅ Step 8 — Clean the repository and dependencies
**What was done**
- Removed all tracked `__pycache__` files and the stray placeholder `files` entries from git (`.gitignore` already excludes caches).
- Removed unused `langgraph`. `pytest` moved to the new `requirements-dev.txt`.
- `project_manifest.json` updated to v0.2.0 with accurate exports.
- Font stack now falls back to system fonts, so the UI still looks right if Google Fonts cannot load.

## ✅ Step 9 — Expand tests
**What was done** (`tests/test_pipeline.py`): grew from 2 to **23 passing tests**, covering duration scaling, topic/difficulty adaptation, each quality check, the feedback loop, the ZIP and PDF exports, special characters, Gemini key handling, retries, error translation and fallback.
Run with `pip install -r requirements-dev.txt && pytest -q`.

## 🟡 Step 10 — Final documentation, deployment and demo polish
**Done**
- README: badges, highlights, sample-output link, updated structure, "Limitations & roadmap", instructor-review disclaimer (also shown in the Export tab).
- `docs/ARCHITECTURE.md` (10 checks, feedback loop, reliability), `docs/USER_GUIDE.md` and `docs/DEMO_SCRIPT.md` rewritten for the new behaviour.
- `examples/Sample_Course_Package.zip` is a pre-generated fallback for the demo (`.gitignore` exception added).

**Remaining (manual, needs the owner)**
- 🔲 Deploy to Streamlit Community Cloud and paste the live URL into the README placeholder.
- 🔲 Capture 2–3 screenshots or a short GIF (landing → generate → results → export) and add them to the README.
- 🔲 Rehearse `docs/DEMO_SCRIPT.md` once end-to-end on the deployed build, (Gemini output was already confirmed live during the bonus round.)

---

## ✅ Bonus round — Live Gemini, dark mode, animations, rotating preview
**What was done**
- **Live Gemini:** the key is stored in `.env` (git-ignored, never committed). Real generation was verified end to end (`provider_used: gemini`, 10/10 checks). Found and fixed three real-world issues along the way:
  - the old default model `gemini-2.5-flash` is retired for new keys, so the default is now the self-updating alias `gemini-flash-latest`;
  - the free tier allows about 5 requests/min, so retries now honor Gemini's "retry in Ns" hint;
  - models can return 503 under load, so retries rotate through fallback models (`GEMINI_FALLBACK_MODELS`).
  The form defaults to Gemini when a key is present.
- **Dark mode:** a 🌙 Dark / ☀️ Light toggle in the nav. The CSS was moved to `assets/theme.css` using design tokens, plus `assets/theme_dark.css`, which also restyles Streamlit's own inputs, tabs, expanders and alerts.
- **Animations (sober):** staggered fade-ups on the hero, header and cards, hover lifts, button feedback, tab fades and staggered checklist rows. All are disabled automatically when the OS asks for reduced motion.
- **Rotating preview card:** 4 sample courses (topic · audience · difficulty · duration, objectives, modules, quality check, learning goal) crossfade every 4.5 seconds with progress dots, using pure CSS with no reruns. Once a real course is generated, the card shows that course instead.

**Verified:** real-browser (Edge) screenshots in light and dark: rotation, form, results, validation checklist, and a full Gemini run through the UI.

---

## ✅ Round 3 — Form, navigation and reliability fixes
**What was done**
- **Announcements removed:** the "Read an announcement" button and its page are gone.
- **Dropdowns instead of typing:** Target audience (12 options) and Learning goal (7 options) are now select boxes. Duration and Difficulty stay as dropdowns. The options live in `core/options.py`. Topic is the only free-text field, with examples and a hint that one word is enough.
- **Single-word topics ("python"):** the backend produced valid courses for "python" in both modes, so the failure was not a crash. The likely causes were (a) Gemini's first answer failing the strict quality check, for example by paraphrasing a learning objective, and (b) hitting the free-tier rate limit on repeated tries. Fixes:
  - assessment objectives are now snapped to the closest real objective (`snap_objectives`), which removes the most common false FAIL;
  - the feedback loop allows 2 retries (was 1);
  - the topic is tidied (`python` → `Python`, SQL-style acronyms kept) and validated, and a single word is explicitly allowed;
  - the Gemini prompt tells the model that one-word topics are valid.
  Verified live: "python" with Gemini → PASS.
- **Navigation scrolls:** "Tell us about yourself" and "Try a sample profile" (and the same buttons on How it works, plus New course) now smooth-scroll to the form. Generating scrolls to the results. A hidden bug was fixed here: Streamlit re-used an identical scroll script, so a second click did nothing, and each request now carries a unique token. Verified in a real browser for all cases.
- **Polish:** the status box warns that Gemini takes about 30 s; the self-correction tick box is labelled "Demo / Mock mode only"; mock text now reads naturally with the fixed goals and audiences.

**Verified:** 35 tests pass (12 new: topic cleaning and validation, every audience × goal combination, sample profile options, objective snapping), plus real-browser checks of the form, scrolling and a live Gemini run.

---

## Out of scope (kept simple on purpose)
Accounts, databases, LMS integration, multi-LLM orchestration, analytics dashboards and multilingual support.

## Known notes
- Never commit `.env` (it holds the API key). On Streamlit Cloud, put `GEMINI_API_KEY` under App Settings → Secrets.
- `st.components.v1.html` (used only for the cosmetic auto-scroll) is deprecated in recent Streamlit versions. It is wrapped in a try/except, so the app still works if it is removed; only the scroll would be lost.
