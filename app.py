import html
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from core.orchestrator import generate_course  # noqa: E402  (after load_dotenv so settings see .env)
from core.llm_provider import ProviderError  # noqa: E402
from core.config import settings  # noqa: E402
from core.exporter import build_course_zip, build_markdown, build_pdf  # noqa: E402
from core.utils import mcq_answer_index, clean_topic, validate_topic  # noqa: E402
from core.options import AUDIENCES, LEARNING_GOALS, DURATIONS, DIFFICULTIES, SAMPLE, TOPIC_EXAMPLES  # noqa: E402

st.set_page_config(
    page_title="EduPath-AI — AI-Powered Course Generator",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# EduPath-AI visual system (assets/theme.css + optional assets/theme_dark.css)
# -----------------------------
ASSETS = Path(__file__).parent / "assets"


def load_css(name: str) -> str:
    try:
        return (ASSETS / name).read_text(encoding="utf-8")
    except OSError:
        return ""  # the app still works unstyled if an asset is missing


# -----------------------------
# State
# -----------------------------
def init_state():
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("show_generator", False)
    st.session_state.setdefault("sample", False)
    st.session_state.setdefault("view", "discover")  # discover | how
    st.session_state.setdefault("dark", False)
    st.session_state.setdefault("exports", None)     # cached {"md", "pdf", "zip"} for the current result
    st.session_state.setdefault("scroll_to", None)  # anchor id to smooth-scroll to on the next render


init_state()


def scroll_to_anchor(anchor_id: str):
    """Best-effort smooth scroll to an element id. Purely cosmetic, so any failure is ignored.
    Retries briefly because the target may still be rendering when the script runs."""
    # A changing nonce makes every request a *new* element; otherwise Streamlit reuses the identical
    # iframe from the previous scroll and never re-runs the script.
    st.session_state.scroll_nonce = st.session_state.get("scroll_nonce", 0) + 1
    js = (f"<script>/*{st.session_state.scroll_nonce}*/(function(){{let n=0;const t=setInterval(function(){{"
          f"const el=window.parent.document.getElementById('{anchor_id}');"
          "if(el){el.scrollIntoView({behavior:'smooth',block:'start'});clearInterval(t);}"
          "else if(++n>25){clearInterval(t);}},60);})();</script>")
    try:
        import streamlit.components.v1 as components
        components.html(js, height=0)
    except Exception:
        pass


def consume_scroll(anchor_id: str):
    """Scroll to `anchor_id` once if a button asked for it."""
    if st.session_state.scroll_to == anchor_id:
        st.session_state.scroll_to = None
        scroll_to_anchor(anchor_id)


def toggle_theme():
    st.session_state.dark = not st.session_state.dark


def apply_theme():
    css = load_css("theme.css")
    if st.session_state.dark:
        css += load_css("theme_dark.css")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


apply_theme()


def reset_course():
    """Clear the generated course and reopen an empty form."""
    st.session_state.result = None
    st.session_state.exports = None
    st.session_state.sample = False
    st.session_state.show_generator = True
    st.session_state.view = "discover"
    st.session_state.scroll_to = "generator"


def set_view(view, generator=None, sample=None):
    """Callback used by buttons. Runs before the rerun, so the page updates instantly."""
    st.session_state.view = view
    if generator is not None:
        st.session_state.show_generator = generator
        if generator:
            st.session_state.scroll_to = "generator"
    if sample is not None:
        st.session_state.sample = sample


# -----------------------------
# Header (language button removed)
# -----------------------------
st.markdown(
    '<div class="edu-header"><div class="brand">'
    '<div class="logo">✦</div>'
    '<div class="brand-name">EduPath-AI</div>'
    '<div class="brand-sub">Your Learning Journey, Powered by AI</div>'
    '</div></div>',
    unsafe_allow_html=True,
)

# -----------------------------
# Navigation (real buttons, state-driven)
# -----------------------------
view = st.session_state.view
nav1, nav2, nav3, nav4 = st.columns([1.15, 1.2, 1.4, .9])
with nav1:
    st.button(
        "Discover", key="nav_discover",
        type="primary" if view == "discover" else "secondary",
        on_click=set_view, args=("discover",), use_container_width=True,
    )
with nav2:
    st.button(
        "How it works", key="nav_how",
        type="primary" if view == "how" else "secondary",
        on_click=set_view, args=("how",), use_container_width=True,
    )
with nav3:
    st.button(
        "Tell us about yourself", key="nav_start",
        type="secondary",
        on_click=set_view, args=("discover", True, False), use_container_width=True,
    )
with nav4:
    st.button(
        "☀️ Light" if st.session_state.dark else "🌙 Dark", key="nav_theme",
        type="secondary", on_click=toggle_theme, use_container_width=True,
    )


# -----------------------------
# Reusable sections
# -----------------------------
def render_how_it_works():
    st.markdown('<div class="section-title">How EduPath-AI works</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">The interface is intentionally simple; the complexity stays in the backend agent pipeline.</div>', unsafe_allow_html=True)
    st.write("")

    cols = st.columns(4)
    workflow = [
        ("01", "Curriculum", "Build prerequisites, objectives, modules and roadmap."),
        ("02", "Content", "Create lesson notes, examples, exercises and case studies."),
        ("03", "Assessment", "Generate quizzes, assignments, answer keys and rubrics."),
        ("04", "Quality", "Check alignment, completeness and sequence before export."),
    ]
    for col, (num, title, desc) in zip(cols, workflow):
        with col:
            st.markdown(
                f'<div class="section-card"><div class="step-num">{num}</div>'
                f'<h3 style="margin:8px 0;">{title}</h3>'
                f'<div class="section-copy">{desc}</div></div>',
                unsafe_allow_html=True,
            )


# Sample courses cycled in the empty preview card. Fields mirror the generator form.
SAMPLE_COURSES = [
    # (topic, audience, duration, difficulty, objectives, modules, learning goal)
    ("Python for Bioinformatics", "Undergraduate students", "4 Weeks", "Beginner", 8, 4,
     "Build practical Python skills for biological sequence analysis."),
    ("Digital Marketing Fundamentals", "Small business owners", "6 Weeks", "Beginner", 10, 5,
     "Plan and run a low-budget online campaign that brings in customers."),
    ("Machine Learning with Scikit-learn", "Working software engineers", "8 Weeks", "Intermediate", 12, 6,
     "Train, evaluate and ship a reliable prediction model."),
    ("Scientific Writing for Researchers", "PhD researchers", "2 Weeks", "Advanced", 6, 3,
     "Write a clear, well-structured journal manuscript."),
]


def sample_slide(topic, audience, duration, difficulty, objectives, modules, goal):
    return (
        '<div class="slide">'
        '<div class="preview-head">'
        f'<div class="preview-title">{html.escape(topic)}</div><span class="badge">Sample course</span></div>'
        f'<div class="preview-sub">{html.escape(audience)} · {html.escape(difficulty)} · {html.escape(duration)}</div>'
        '<div class="preview-line"></div>'
        f'<div class="preview-status"><span>Learning objectives</span><b>{objectives} mapped</b></div>'
        f'<div class="preview-status" style="margin-top:11px;"><span>Course modules</span><b>{modules} modules</b></div>'
        '<div class="preview-status" style="margin-top:11px;"><span>Quality check</span><b class="pass">PASS</b></div>'
        f'<div class="next-step"><div class="next-label">LEARNING GOAL</div><div class="next-text">{html.escape(goal)}</div></div>'
        '</div>'
    )


def render_preview_card(result):
    """Right-hand card: rotating sample courses until a course is generated, then the real data."""
    if result:
        title = html.escape(result.curriculum.title)
        subtitle = html.escape(f"{result.request.audience} · {result.request.difficulty} · {result.request.duration}")
        objectives = sum(len(m.learning_objectives) for m in result.curriculum.modules)
        status = result.validation.status
        body = (
            '<div class="preview-head">'
            f'<div class="preview-title">{title}</div><span class="badge badge-done">Generated</span></div>'
            f'<div class="preview-sub">{subtitle}</div>'
            '<div class="preview-line"></div>'
            f'<div class="preview-status"><span>Learning objectives</span><b>{objectives} mapped</b></div>'
            f'<div class="preview-status" style="margin-top:11px;"><span>Course modules</span><b>{len(result.curriculum.modules)} modules</b></div>'
            f'<div class="preview-status" style="margin-top:11px;"><span>Quality check</span>'
            f'<b class="{"pass" if status == "PASS" else "fail"}">{status} · {result.validation.score:.0f}%</b></div>'
            '<div class="next-step"><div class="next-label">NEXT STEP</div>'
            '<div class="next-text">Review the course workspace below, then export the validated package.</div></div>'
        )
        top = '<div class="preview-top"><span>YOUR COURSE</span></div>'
    else:
        body = '<div class="rotor">' + "".join(sample_slide(*c) for c in SAMPLE_COURSES) + "</div>"
        top = ('<div class="preview-top"><span>AI COURSE PREVIEW</span>'
               f'<span class="dots">{"<i></i>" * len(SAMPLE_COURSES)}</span></div>')

    note = "" if result else '<div class="sample-note">Sample courses. Fill in the form to build your own.</div>'
    st.markdown(f'<div class="hero-wrap"><div class="preview">{top}{body}{note}</div></div>', unsafe_allow_html=True)


def render_footer():
    st.markdown(
        '<div class="footer">EduPath-AI · Autonomous Multi-Agent Course & Training Curriculum Generator · Built for the hackathon MVP</div>',
        unsafe_allow_html=True,
    )


# -----------------------------
# Page views
# -----------------------------
view = st.session_state.view

if view == "how":
    st.write("")
    render_how_it_works()
    st.write("")
    st.button("Tell us about yourself  →", key="how_cta", type="primary",
              on_click=set_view, args=("discover", True, False))
    render_footer()
    st.stop()

# ---- Discover view ----
result = st.session_state.result

left, right = st.columns([1.06, .94], gap="large")
with left:
    st.markdown(
        '<div class="hero-wrap">'
        '<div class="eyebrow">AI-POWERED COURSE GENERATOR</div>'
        '<h1 class="hero-title">Build learning paths that fit<br><span>your goals.</span></h1>'
        '<div class="hero-copy">Create personalized courses, lessons and assessments from one learning goal — '
        'coordinated by specialized AI agents and checked through a dedicated quality layer.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    b1, b2 = st.columns(2)
    with b1:
        st.button("Tell us about yourself  →", key="hero_start", type="primary",
                  on_click=set_view, args=("discover", True, False), use_container_width=True)
    with b2:
        st.button("Try a sample profile", key="hero_sample",
                  on_click=set_view, args=("discover", True, True), use_container_width=True)

with right:
    render_preview_card(result)

st.markdown("""
<div class="feature-strip">
  <div class="feature"><span class="check">✓</span> Multi-agent generation</div>
  <div class="feature"><span class="check">✓</span> Structured outputs</div>
  <div class="feature"><span class="check">✓</span> Quality validation</div>
  <div class="feature"><span class="check">✓</span> Downloadable course package</div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Generator
# -----------------------------
if st.session_state.show_generator:
    st.markdown('<div id="generator" class="anchor"></div>', unsafe_allow_html=True)
    consume_scroll("generator")
    st.markdown('<div class="section-title">Tell us about your learning goal</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Pick a few options and name a topic. EduPath-AI will coordinate the curriculum, content, assessment and quality agents.</div>', unsafe_allow_html=True)
    st.write("")

    sample = st.session_state.sample
    pick = lambda options, key, default=0: options.index(SAMPLE[key]) if sample else default  # noqa: E731
    with st.form("course_form"):
        c1, c2 = st.columns(2)
        with c1:
            topic = st.text_input(
                "Topic", value=SAMPLE["topic"] if sample else "", max_chars=80,
                placeholder="e.g. " + ", ".join(TOPIC_EXAMPLES[:3]),
                help="A single word is fine, e.g. Python or Photosynthesis. You don't need to add the word 'course'.",
            )
            audience = st.selectbox("Target audience", AUDIENCES, index=pick(AUDIENCES, "audience", 2))
            duration = st.selectbox("Duration", DURATIONS, index=pick(DURATIONS, "duration", 2))
        with c2:
            difficulty = st.selectbox("Difficulty", DIFFICULTIES, index=pick(DIFFICULTIES, "difficulty", 0))
            goal = st.selectbox("Learning goal", LEARNING_GOALS, index=pick(LEARNING_GOALS, "goal", 0))
            mode = st.radio("Generation mode", ["Demo / Mock — no API key", "Gemini API"],
                            index=1 if settings.gemini_configured else 0, horizontal=True)
            if settings.gemini_configured:
                st.caption("Gemini API key detected. If Gemini is unavailable, demo output is used instead.")
            else:
                st.caption("No GEMINI_API_KEY configured — Gemini mode will fall back to demo output.")
            demo_loop = st.checkbox(
                "Demonstrate self-correction (Demo / Mock mode only)",
                help="The first attempt is deliberately flawed so you can watch the Quality agent catch it and the agents fix it.",
            )
        generate = st.form_submit_button("Generate Course", type="primary", use_container_width=True)

    if generate:
        topic_clean = clean_topic(topic)
        topic_error = validate_topic(topic_clean)
        if topic_error:
            st.error(topic_error)
        else:
            provider = "gemini" if mode.startswith("Gemini") else "mock"
            try:
                with st.status("EduPath-AI is coordinating the agents… (Gemini takes about 30 seconds)" if provider == "gemini" else "EduPath-AI is coordinating the agents…", expanded=True) as status:
                    def on_step(agent, state, detail):
                        if state == "running":
                            st.write(f"⏳ **{agent}** working… {detail}")
                        else:
                            st.write(f"✅ **{agent}** — {detail}")

                    new_result = generate_course(
                        provider, topic_clean, audience, duration,
                        difficulty, goal, on_step=on_step,
                        inject_fault=demo_loop and provider == "mock",
                    )
                    # Build the export files once per course, not on every Streamlit rerun.
                    md, pdf = build_markdown(new_result), build_pdf(new_result)
                    st.session_state.exports = {
                        "md": md, "pdf": pdf, "zip": build_course_zip(new_result, md, pdf),
                    }
                    status.update(label="Course package generated", state="complete", expanded=False)
                st.session_state.result = new_result
                st.session_state.scroll_to = "workspace"
                st.rerun()  # refresh so the preview card shows the new course
            except ProviderError as exc:
                st.error(str(exc))
                if exc.details:
                    with st.expander("Technical details"):
                        st.code(exc.details)
            except Exception as exc:  # last resort: never show a raw stack trace to the user
                st.error("Something went wrong while generating the course. Please try again.")
                with st.expander("Technical details"):
                    st.code(f"{type(exc).__name__}: {exc}")

result = st.session_state.result

if result:
    st.divider()
    st.markdown('<div id="workspace" class="anchor"></div>', unsafe_allow_html=True)
    consume_scroll("workspace")

    head_l, head_r = st.columns([3, 1])
    with head_l:
        st.markdown('<div class="section-title">Course workspace</div>', unsafe_allow_html=True)
    with head_r:
        st.button("↺ New course", key="new_course", on_click=reset_course, use_container_width=True)

    if result.notice:
        st.warning(result.notice)
        if result.notice_details:
            with st.expander("Technical details"):
                st.code(result.notice_details)

    validation = result.validation
    cols = st.columns(4)
    metrics = [
        ("Validation", f"{validation.status} · {validation.score:.0f}%"),
        ("Modules", len(result.curriculum.modules)),
        ("Lessons", len(result.lessons.lessons)),
        ("Assessments", len(result.assessments.items)),
    ]
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.markdown(
                f'<div class="metric-card"><div class="metric-label">{label}</div>'
                f'<div class="metric-value">{value}</div></div>',
                unsafe_allow_html=True
            )

    st.write("")
    if validation.status == "PASS":
        extra = f" after {validation.attempts} attempts (self-corrected)" if validation.attempts > 1 else ""
        st.success(f"Quality & Validation Agent: PASS{extra} — the package is ready for export.")
    else:
        st.error("Quality & Validation Agent: FAIL — see the Validation tab for details.")

    tabs = st.tabs(["Curriculum", "Lessons", "Assessments", "Validation", "Export"])

    with tabs[0]:
        st.subheader(result.curriculum.title)
        st.write(result.curriculum.description)
        if result.curriculum.prerequisites:
            st.markdown("**Prerequisites**")
            for item in result.curriculum.prerequisites:
                st.write("•", item)
        if result.curriculum.roadmap:
            st.markdown("**Roadmap**")
            st.markdown(
                '<div class="timeline">' + "".join(
                    f'<div class="timeline-item">{html.escape(step)}</div>' for step in result.curriculum.roadmap
                ) + "</div>", unsafe_allow_html=True)
        st.markdown("**Modules**")
        for module in result.curriculum.modules:
            with st.expander(f"Module {module.number}: {module.title}"):
                st.write(module.summary)
                st.write("**Learning objectives**")
                for objective in module.learning_objectives:
                    st.write("•", objective)

    with tabs[1]:
        for lesson in result.lessons.lessons:
            with st.expander(f"Lesson {lesson.module_number}.{lesson.lesson_number} — {lesson.title}"):
                st.markdown(lesson.notes)
                st.write("**Examples**")
                for x in lesson.examples:
                    st.write("•", x)
                st.write("**Exercises**")
                for x in lesson.exercises:
                    st.write("•", x)
                if lesson.case_study:
                    st.info(f"**Case study:** {lesson.case_study}")

    with tabs[2]:
        for item in result.assessments.items:
            with st.expander(f"{item.type.upper()} — {item.title}"):
                st.write(item.prompt)
                correct = mcq_answer_index(item.answer, item.options) if item.options else -1
                for i, option in enumerate(item.options):
                    cls = "opt correct" if i == correct else "opt"
                    mark = " ✓" if i == correct else ""
                    st.markdown(f'<div class="{cls}">{chr(65+i)}. {html.escape(option)}{mark}</div>', unsafe_allow_html=True)
                if not item.options:
                    st.write("**Answer:**", item.answer)
                st.write("**Mapped objective:**", item.learning_objective)
                if item.rubric:
                    st.write("**Rubric:**", item.rubric)

    with tabs[3]:
        pill_cls = "score-pill" if validation.status == "PASS" else "score-pill bad"
        passed = sum(c.passed for c in validation.checks)
        st.markdown(
            f'<span class="{pill_cls}">{validation.status} · {validation.score:.0f}% — '
            f'{passed}/{len(validation.checks)} checks passed</span>', unsafe_allow_html=True)
        st.write("")
        for check in validation.checks:
            ok = check.passed
            detail = f'<div class="check-detail">{html.escape(check.detail)}</div>' if check.detail else ""
            st.markdown(
                f'<div class="check-row {"ok" if ok else "bad"}"><span class="mark">{"✓" if ok else "✗"}</span>'
                f'<div>{html.escape(check.name)}{detail}</div></div>', unsafe_allow_html=True)
        if validation.attempts > 1:
            st.markdown(f"**Feedback loop:** the package passed after **{validation.attempts} attempts**. "
                        "Problems found and fixed automatically:")
            for issue in validation.resolved_issues:
                st.write("•", issue)
        st.markdown("**Feedback**")
        for line in validation.feedback:
            st.write("•", line)
        with st.expander("Raw validation report (JSON)"):
            st.json(validation.model_dump())

    with tabs[4]:
        st.write("Export the complete validated course package, or download a single file.")
        exports = st.session_state.exports
        if exports:
            st.download_button(
                "Download Course_Package.zip", data=exports["zip"], file_name="Course_Package.zip",
                mime="application/zip", type="primary", use_container_width=True,
            )
            d1, d2 = st.columns(2)
            with d1:
                st.download_button("Download PDF", data=exports["pdf"], file_name="Complete_Course.pdf",
                                   mime="application/pdf", use_container_width=True)
            with d2:
                st.download_button("Download Markdown", data=exports["md"], file_name="Complete_Course.md",
                                   mime="text/markdown", use_container_width=True)
            st.caption("The ZIP contains: Complete_Course (PDF + MD), Lessons.md, Answer_Key.md, "
                       "Curriculum.json, Assessments.json and Validation_Report.json.")
        st.caption("AI-generated content should be reviewed by an instructor before classroom use.")

# -----------------------------
# How it works (bottom of Discover page)
# -----------------------------
st.divider()
render_how_it_works()
render_footer()
