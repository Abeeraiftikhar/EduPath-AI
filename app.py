import html

import streamlit as st
from dotenv import load_dotenv

from core.orchestrator import CourseOrchestrator
from core.config import settings
from core.exporter import build_course_zip

load_dotenv()

st.set_page_config(
    page_title="EduPath-AI — AI-Powered Course Generator",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# EduPath-AI visual system
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

:root {
    --blue:#2563EB;
    --blue-dark:#1D4ED8;
    --blue-deep:#172554;
    --blue-soft:#EFF6FF;
    --blue-pale:#F8FBFF;
    --text:#0F172A;
    --muted:#64748B;
    --border:#E2E8F0;
    --white:#FFFFFF;
    --success:#059669;
    --warning:#D97706;
}

html, body, [class*="css"] {
    font-family:'DM Sans', sans-serif;
}

.stApp {
    background:linear-gradient(180deg,#F8FBFF 0%,#FFFFFF 55%,#F8FBFF 100%);
    color:var(--text);
}

#MainMenu, footer, header { visibility:hidden; }
.block-container {
    max-width:1180px;
    padding:1.1rem 1.5rem 3rem;
}

/* Header */
.edu-header {
    background:rgba(255,255,255,.94);
    border:1px solid var(--border);
    border-radius:18px;
    padding:14px 18px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    box-shadow:0 5px 22px rgba(37,99,235,.05);
    margin-bottom:14px;
}
.brand {
    display:flex;
    align-items:center;
    gap:12px;
}
.logo {
    width:38px;
    height:38px;
    border-radius:12px;
    background:linear-gradient(135deg,var(--blue),#60A5FA);
    display:flex;
    align-items:center;
    justify-content:center;
    color:white;
    font-size:20px;
    font-weight:700;
}
.brand-name {
    font-size:22px;
    font-weight:700;
    color:var(--blue-deep);
}
.brand-sub {
    margin-left:4px;
    padding-left:14px;
    border-left:1px solid var(--border);
    color:var(--muted);
    font-size:13px;
}

/* Hero */
.hero-wrap {
    padding:58px 0 35px;
}
.eyebrow {
    color:var(--blue);
    font-size:12px;
    font-weight:700;
    letter-spacing:3px;
    text-transform:uppercase;
    margin-bottom:18px;
}
.hero-title {
    color:var(--text);
    font-size:54px;
    line-height:1.05;
    letter-spacing:-2.3px;
    font-weight:700;
    margin:0;
}
.hero-title span { color:var(--blue); }
.hero-copy {
    color:#53657D;
    font-size:18px;
    line-height:1.65;
    max-width:680px;
    margin-top:22px;
}
.preview {
    background:white;
    border:1px solid #CFE0FF;
    border-radius:22px;
    padding:22px;
    box-shadow:0 18px 45px rgba(37,99,235,.11);
    margin-top:10px;
}
.preview-top {
    color:#8AA0BC;
    font-size:11px;
    letter-spacing:2px;
    font-weight:700;
}
.preview-title {
    color:#183153;
    font-size:23px;
    font-weight:700;
    margin-top:9px;
}
.preview-sub { color:#7890AE; font-size:13px; }
.preview-line {
    height:1px;
    background:#E8EEF7;
    margin:16px 0;
}
.preview-status {
    display:flex;
    justify-content:space-between;
    color:#60748F;
    font-size:13px;
}
.badge {
    display:inline-block;
    padding:6px 10px;
    border-radius:20px;
    background:#EFF6FF;
    color:var(--blue);
    font-size:11px;
    font-weight:700;
    white-space:nowrap;
}
.badge-done { background:#ECFDF5; color:#059669; }
.next-step {
    background:#F0F7FF;
    border-radius:14px;
    padding:15px;
    margin-top:16px;
}
.next-label {
    color:#6C87A8;
    font-size:10px;
    letter-spacing:1.5px;
    font-weight:700;
}
.next-text { color:#49627F; font-size:13px; margin-top:5px; }

/* Buttons */
div.stButton > button,
div.stDownloadButton > button,
button[kind="primary"] {
    border-radius:11px !important;
    min-height:44px !important;
    font-weight:600 !important;
    border:1px solid #CFE0FF !important;
}
div.stButton > button[kind="primary"],
div.stDownloadButton > button[kind="primary"],
div.stFormSubmitButton > button[kind="primary"] {
    background:var(--blue) !important;
    color:white !important;
}
div.stButton > button[kind="primary"]:hover,
div.stDownloadButton > button[kind="primary"]:hover,
div.stFormSubmitButton > button[kind="primary"]:hover {
    background:var(--blue-dark) !important;
}
div.stButton > button[kind="secondary"] {
    background:white !important;
    color:#475569 !important;
}
div.stButton > button[kind="secondary"]:hover {
    background:var(--blue-soft) !important;
    color:var(--blue) !important;
}

/* Feature strip */
.feature-strip {
    border-top:1px solid var(--border);
    border-bottom:1px solid var(--border);
    padding:22px 0;
    margin:28px 0 45px;
    display:flex;
    gap:55px;
    color:#60748F;
    font-size:14px;
}
.feature { display:flex; gap:9px; align-items:center; }
.check { color:var(--blue); font-weight:700; }

/* Sections */
.section-card {
    background:white;
    border:1px solid var(--border);
    border-radius:20px;
    padding:28px;
    box-shadow:0 8px 28px rgba(15,23,42,.035);
    margin-bottom:20px;
}
.section-title { font-size:27px; font-weight:700; color:var(--text); }
.section-copy { color:var(--muted); line-height:1.6; }

.announce-date {
    color:var(--blue);
    font-size:12px;
    font-weight:700;
    letter-spacing:1.5px;
    text-transform:uppercase;
}
.announce-title { font-size:19px; font-weight:700; color:var(--text); margin:6px 0; }

/* Streamlit form controls */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
    border-radius:11px !important;
    border-color:#D7E1EF !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stRadio label {
    color:#334155 !important;
    font-weight:600 !important;
}

/* Results */
.metric-card {
    background:#fff;
    border:1px solid var(--border);
    border-radius:15px;
    padding:15px;
    text-align:center;
}
.metric-label { color:var(--muted); font-size:12px; }
.metric-value { color:var(--blue-deep); font-size:22px; font-weight:700; }

.footer {
    text-align:center;
    color:#94A3B8;
    font-size:12px;
    padding-top:28px;
}
@media (max-width: 850px) {
    .hero-title { font-size:39px; }
    .feature-strip { gap:18px; flex-wrap:wrap; }
    .brand-sub { display:none; }
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# State
# -----------------------------
def init_state():
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("show_generator", False)
    st.session_state.setdefault("sample", False)
    st.session_state.setdefault("view", "discover")  # discover | announcement | how


init_state()


def set_view(view, generator=None, sample=None):
    """Callback used by buttons. Runs before the rerun, so the page updates instantly."""
    st.session_state.view = view
    if generator is not None:
        st.session_state.show_generator = generator
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
nav1, nav2, nav3, nav4 = st.columns([1.15, 1.4, 1.2, 1.3])
with nav1:
    st.button(
        "Discover", key="nav_discover",
        type="primary" if view == "discover" else "secondary",
        on_click=set_view, args=("discover",), use_container_width=True,
    )
with nav2:
    st.button(
        "Read an announcement", key="nav_announcement",
        type="primary" if view == "announcement" else "secondary",
        on_click=set_view, args=("announcement",), use_container_width=True,
    )
with nav3:
    st.button(
        "How it works", key="nav_how",
        type="primary" if view == "how" else "secondary",
        on_click=set_view, args=("how",), use_container_width=True,
    )
with nav4:
    st.button(
        "Tell us about yourself", key="nav_start",
        type="secondary",
        on_click=set_view, args=("discover", True, False), use_container_width=True,
    )


# -----------------------------
# Reusable sections
# -----------------------------
ANNOUNCEMENTS = [
    # Edit these entries to change what appears under "Read an announcement".
    ("Version 1.0", "EduPath-AI MVP is live",
     "Generate a full course package — curriculum, lessons, assessments and a quality report — from a single learning goal."),
    ("Demo mode", "Try it without an API key",
     "Choose “Demo / Mock” in the generator to explore the full workflow instantly. Switch to Gemini API for AI-written content."),
    ("Quality layer", "Every package is validated",
     "A dedicated Quality agent checks alignment, completeness and sequence before you export your course as a ZIP."),
]


def render_announcements():
    st.write("")
    st.markdown('<div class="section-title">Announcements</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">The latest news about EduPath-AI.</div>', unsafe_allow_html=True)
    st.write("")
    for date, title, body in ANNOUNCEMENTS:
        st.markdown(
            f'<div class="section-card"><div class="announce-date">{html.escape(date)}</div>'
            f'<div class="announce-title">{html.escape(title)}</div>'
            f'<div class="section-copy">{html.escape(body)}</div></div>',
            unsafe_allow_html=True,
        )
    st.button("Tell us about yourself  →", key="ann_cta", type="primary",
              on_click=set_view, args=("discover", True, False))


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
                f'<div class="section-card"><div style="color:#2563EB;font-weight:700;">{num}</div>'
                f'<h3 style="margin:8px 0;color:#0F172A;">{title}</h3>'
                f'<div class="section-copy">{desc}</div></div>',
                unsafe_allow_html=True,
            )


def render_preview_card(result):
    """Right-hand card. Shows placeholders until a course is generated, then real data."""
    if result:
        title = html.escape(result.curriculum.title)
        subtitle = html.escape(result.request.audience + " · " + result.request.difficulty)
        objectives = sum(len(m.learning_objectives) for m in result.curriculum.modules)
        modules = len(result.curriculum.modules)
        status = result.validation.status
        status_color = "#059669" if status == "PASS" else "#DC2626"
        badge = '<span class="badge badge-done">Generated</span>'
        next_text = "Review the course workspace below, then export the validated package."
        obj_text, mod_text = f"{objectives} mapped", f"{modules} modules"
    else:
        title = "Your course preview"
        subtitle = "Fill in the form to generate a structured learning path"
        status, status_color = "Pending", "#8AA0BC"
        badge = '<span class="badge">Ready to generate</span>'
        next_text = "Generate lessons, assessments, answer keys and rubrics from the validated curriculum."
        obj_text, mod_text = "—", "—"

    st.markdown(
        '<div class="hero-wrap"><div class="preview">'
        '<div class="preview-top">AI COURSE PREVIEW</div>'
        '<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;">'
        f'<div class="preview-title">{title}</div>{badge}</div>'
        f'<div class="preview-sub">{subtitle}</div>'
        '<div class="preview-line"></div>'
        f'<div class="preview-status"><span>Learning objectives</span><b>{obj_text}</b></div>'
        f'<div class="preview-status" style="margin-top:11px;"><span>Course modules</span><b>{mod_text}</b></div>'
        f'<div class="preview-status" style="margin-top:11px;"><span>Quality check</span><b style="color:{status_color};">{status}</b></div>'
        f'<div class="next-step"><div class="next-label">NEXT STEP</div><div class="next-text">{next_text}</div></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        '<div class="footer">EduPath-AI · Autonomous Multi-Agent Course & Training Curriculum Generator · Built for the hackathon MVP</div>',
        unsafe_allow_html=True,
    )


# -----------------------------
# Page views
# -----------------------------
view = st.session_state.view

if view == "announcement":
    render_announcements()
    render_footer()
    st.stop()

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
    st.markdown('<div class="section-title">Tell us about your learning goal</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Provide the basic course requirements. EduPath-AI will coordinate the curriculum, content, assessment and quality agents.</div>', unsafe_allow_html=True)
    st.write("")

    sample = st.session_state.sample
    with st.form("course_form"):
        c1, c2 = st.columns(2)
        with c1:
            topic = st.text_input("Topic", value="Python for Bioinformatics" if sample else "", placeholder="e.g. Python for Bioinformatics")
            audience = st.text_input("Target audience", value="Undergraduate students" if sample else "", placeholder="e.g. Undergraduate students")
            duration = st.selectbox("Duration", ["1 Week", "2 Weeks", "4 Weeks", "6 Weeks", "8 Weeks", "12 Weeks"], index=2)
        with c2:
            difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"], index=1 if sample else 0)
            goal = st.text_area("Learning goal", value="Build practical Python skills for biological sequence analysis." if sample else "", height=112)
            mode = st.radio("Generation mode", ["Demo / Mock — no API key", "Gemini API"], horizontal=True)
        generate = st.form_submit_button("Generate Course", type="primary", use_container_width=True)

    if generate:
        if not topic.strip() or not audience.strip() or not goal.strip():
            st.error("Please complete Topic, Target audience and Learning goal.")
        else:
            try:
                with st.status("EduPath-AI is coordinating the agents...", expanded=True) as status:
                    provider = "gemini" if mode.startswith("Gemini") else "mock"
                    orchestrator = CourseOrchestrator(provider=provider)
                    new_result = orchestrator.generate(
                        topic.strip(), audience.strip(), duration,
                        difficulty, goal.strip()
                    )
                    status.update(label="Course package generated", state="complete")
                st.session_state.result = new_result
                st.rerun()  # refresh so the preview card shows the new course
            except Exception as exc:
                st.error(f"Generation failed: {exc}")

result = st.session_state.result

if result:
    st.divider()
    st.markdown('<div class="section-title">Course workspace</div>', unsafe_allow_html=True)

    validation = result.validation
    cols = st.columns(4)
    metrics = [
        ("Validation", validation.status),
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

    if validation.status == "PASS":
        st.success("Quality & Validation Agent: PASS — the package is ready for export.")
    else:
        st.error("Quality & Validation Agent: FAIL")
        for issue in validation.issues:
            st.write("•", issue)

    tabs = st.tabs(["Curriculum", "Lessons", "Assessments", "Validation", "Export"])

    with tabs[0]:
        st.subheader(result.curriculum.title)
        st.write(result.curriculum.description)
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

    with tabs[2]:
        for item in result.assessments.items:
            with st.expander(f"{item.type.upper()} — {item.title}"):
                st.write(item.prompt)
                if item.options:
                    for i, option in enumerate(item.options):
                        st.write(f"{chr(65+i)}. {option}")
                st.write("**Answer:**", item.answer)
                st.write("**Mapped objective:**", item.learning_objective)
                if item.rubric:
                    st.write("**Rubric:**", item.rubric)

    with tabs[3]:
        st.json(validation.model_dump())

    with tabs[4]:
        st.write("Export the complete validated course package.")
        package = build_course_zip(result)
        st.download_button(
            "Download Course_Package.zip",
            data=package,
            file_name="Course_Package.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True,
        )

# -----------------------------
# How it works (bottom of Discover page)
# -----------------------------
st.divider()
render_how_it_works()
render_footer()
