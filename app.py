import base64
import html
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from core.orchestrator import generate_course  # noqa: E402  (after load_dotenv so settings see .env)
from core.llm_provider import ProviderError  # noqa: E402
from core.config import settings  # noqa: E402
from core.exporter import build_course_zip, build_markdown, build_pdf  # noqa: E402
from core.utils import mcq_answer_index, clean_topic, validate_topic  # noqa: E402
from core.options import (  # noqa: E402
    AUDIENCES, LEARNING_GOALS, DURATIONS, DIFFICULTIES, WEEKLY_HOURS, LEVEL_HINTS, SAMPLE, TOPIC_EXAMPLES,
)
from ui import sections as ui  # noqa: E402

ROOT = Path(__file__).parent
ASSETS = ROOT / "assets"


def _favicon():
    try:
        from PIL import Image
        return Image.open(ASSETS / "favicon.png")
    except Exception:
        return "🔷"


st.set_page_config(
    page_title="EduPath-AI — Build a Learning Path That Fits You",
    page_icon=_favicon(),
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# State
# -----------------------------
MODE_DEMO = "Demo / Mock — no API key"
MODE_GEMINI = "Gemini API"

WIZ_DEFAULT = {
    "topic": "", "audience": AUDIENCES[2], "difficulty": "Beginner", "goal": LEARNING_GOALS[0],
    "duration": "4 Weeks", "hours": WEEKLY_HOURS[1],
    "mode": MODE_GEMINI if settings.gemini_configured else MODE_DEMO, "demo": False,
}
WIDGET_KEYS = {  # wizard field -> widget key
    "topic": "w_topic", "audience": "w_audience", "difficulty": "w_difficulty", "goal": "w_goal",
    "duration": "w_duration", "hours": "w_hours", "mode": "w_mode", "demo": "w_demo",
}


def init_state():
    ss = st.session_state
    ss.setdefault("dark", True)
    ss.setdefault("show_generator", False)
    ss.setdefault("wiz", dict(WIZ_DEFAULT))
    ss.setdefault("wiz_step", 1)
    ss.setdefault("wiz_error", None)
    ss.setdefault("pending", None)       # inputs waiting to be generated on this run
    ss.setdefault("last_inputs", None)   # for "Regenerate"
    ss.setdefault("result", None)
    ss.setdefault("exports", None)       # cached {"md", "pdf", "zip"} for the current result
    ss.setdefault("scroll_to", None)     # anchor id to smooth-scroll to on the next render


init_state()


# -----------------------------
# Theme
# -----------------------------
def load_css(name: str) -> str:
    try:
        return (ASSETS / name).read_text(encoding="utf-8")
    except OSError:
        return ""  # the app still works unstyled if an asset is missing


def logo_uri(dark: bool) -> str:
    """The brand mark as a data URI. Dark theme gets the lighter tint of the same blue for contrast."""
    try:
        data = (ASSETS / "brand" / ("logo_mark_dark.png" if dark else "logo_mark.png")).read_bytes()
        return "url(data:image/png;base64," + base64.b64encode(data).decode() + ")"
    except OSError:
        return "none"  # no logo file: the wordmark text still shows


def apply_theme():
    css = f":root{{--logo-img:{logo_uri(st.session_state.dark)};}}" + load_css("icons.css") + load_css("theme.css")
    if st.session_state.dark:
        css += load_css("theme_dark.css")
    icon = "sun" if st.session_state.dark else "moon"   # shows the mode you would switch TO
    css += f".st-key-nav_theme button p::before{{--m:var(--ic-{icon});}}"
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


apply_theme()


# -----------------------------
# Helpers: scrolling and callbacks
# -----------------------------
def scroll_to_anchor(anchor_id: str):
    """Best-effort smooth scroll. Purely cosmetic, so any failure is ignored. Retries briefly because the
    target may still be rendering; the nonce makes each request a new element (Streamlit would otherwise
    reuse the identical iframe and never re-run the script)."""
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
    if st.session_state.scroll_to == anchor_id:
        st.session_state.scroll_to = None
        scroll_to_anchor(anchor_id)


def toggle_theme():
    st.session_state.dark = not st.session_state.dark


def save_wizard():
    """Copy live widget values into the wizard dict (widgets of other steps are not mounted)."""
    wiz = st.session_state.wiz
    for field, key in WIDGET_KEYS.items():
        value = st.session_state.get(key)
        if value is not None:
            wiz[field] = value


def open_wizard(step=1, sample=False):
    if sample:
        st.session_state.wiz = {**WIZ_DEFAULT, **{k: SAMPLE[k] for k in ("topic", "audience", "duration", "difficulty", "goal", "hours")}}
    for key in WIDGET_KEYS.values():           # drop stale widget state so values come from `wiz`
        st.session_state.pop(key, None)
    st.session_state.wiz_step = step
    st.session_state.wiz_error = None
    st.session_state.show_generator = True
    st.session_state.scroll_to = "generator"


def go_step(step: int):
    save_wizard()
    wiz = st.session_state.wiz
    if st.session_state.wiz_step == 1 and step > 1:       # validate the topic before leaving step 1
        topic = clean_topic(wiz["topic"])
        error = validate_topic(topic)
        if error:
            st.session_state.wiz_error = error
            return
        wiz["topic"] = topic
    st.session_state.wiz_error = None
    st.session_state.wiz_step = step


def start_build():
    save_wizard()
    wiz = st.session_state.wiz
    topic = clean_topic(wiz["topic"])
    error = validate_topic(topic)
    if error:
        st.session_state.wiz_step, st.session_state.wiz_error = 1, error
        return
    wiz["topic"] = topic
    st.session_state.pending = dict(wiz)
    st.session_state.scroll_to = "progress"


def regenerate():
    if st.session_state.last_inputs:
        st.session_state.pending = dict(st.session_state.last_inputs)
        st.session_state.scroll_to = "progress"


def reset_course():
    st.session_state.result = None
    st.session_state.exports = None
    st.session_state.wiz = dict(WIZ_DEFAULT)
    open_wizard(1)


# -----------------------------
# Navigation (sticky, glass)
# -----------------------------
with st.container(key="topnav"):
    n0, n1, n2, _gap, n3, n4 = st.columns([2.1, 1.05, 1.3, 1.2, 2.1, .55], vertical_alignment="center")
    with n0:
        st.html(ui.brand())
    with n1:
        st.button("Discover", key="nav_discover_on", use_container_width=True,
                  on_click=lambda: st.session_state.update(scroll_to="top"))
    with n2:
        st.button("How it works", key="nav_how", use_container_width=True,
                  on_click=lambda: st.session_state.update(scroll_to="how"))
    with n3:
        st.button("Tell us about yourself", key="cta_nav", type="primary", use_container_width=True,
                  on_click=open_wizard)
    with n4:
        st.button("Theme", key="nav_theme", use_container_width=True, on_click=toggle_theme,
                  help="Switch between dark and light mode")

st.html('<div id="top" class="anchor"></div>')
consume_scroll("top")

# -----------------------------
# Hero
# -----------------------------
result = st.session_state.result
left, right = st.columns([1.05, .95], gap="large")
with left:
    st.html(ui.hero_copy())
    b1, b2 = st.columns(2)
    with b1:
        st.button("Build my learning path", key="cta_hero", type="primary", use_container_width=True, on_click=open_wizard)
    with b2:
        st.button("Explore a sample", key="hero_sample", use_container_width=True,
                  on_click=lambda: open_wizard(5, sample=True))
    st.html(ui.trust_row())
with right:
    st.html(ui.preview_card(result))


# -----------------------------
# Onboarding wizard
# -----------------------------
def render_wizard():
    st.html('<div id="generator" class="anchor"></div>')
    consume_scroll("generator")
    step, wiz = st.session_state.wiz_step, st.session_state.wiz

    def init(field):  # seed a widget from the wizard dict when it is not mounted yet
        st.session_state.setdefault(WIDGET_KEYS[field], wiz[field])

    with st.container(key="wizard"):
        st.html(ui.pips(step))
        if step == 1:
            st.html(ui.step_heading("What do you want to learn?", "A single word works. Try “Python”, “Photosynthesis” or “Public Speaking”."))
            init("topic"); init("audience")
            st.text_input("Topic", key="w_topic", max_chars=80, placeholder="e.g. " + ", ".join(TOPIC_EXAMPLES[:3]))
            st.selectbox("Who is this for?", AUDIENCES, key="w_audience")
            if st.session_state.wiz_error:
                st.error(st.session_state.wiz_error)
        elif step == 2:
            st.html(ui.step_heading("What is your current level?", "This sets the depth of the lessons and the strength of the objectives."))
            init("difficulty")
            st.pills("Level", DIFFICULTIES, key="w_difficulty", label_visibility="collapsed",
                     format_func=lambda d: f"{d} · {LEVEL_HINTS[d]}")
        elif step == 3:
            st.html(ui.step_heading("What is your goal?", "Pick the outcome that matters most. The course is shaped around it."))
            init("goal")
            st.pills("Goal", LEARNING_GOALS, key="w_goal", label_visibility="collapsed")
        elif step == 4:
            st.html(ui.step_heading("How much time do you have?", "We size the number of modules and the workload to your schedule."))
            init("duration"); init("hours")
            st.markdown("**Course length**")
            st.pills("Duration", DURATIONS, key="w_duration", label_visibility="collapsed")
            st.markdown("**Weekly time**")
            st.pills("Weekly time", WEEKLY_HOURS, key="w_hours", label_visibility="collapsed")
        else:
            st.html(ui.step_heading("Review and build", "Everything below shapes your learning path. Go back to change anything."))
            st.html(ui.summary([
                ("Topic", wiz["topic"] or "—"), ("Audience", wiz["audience"]), ("Level", wiz["difficulty"]),
                ("Goal", wiz["goal"]), ("Course length", wiz["duration"]), ("Weekly time", wiz["hours"]),
            ]))
            init("mode"); init("demo")
            st.radio("Generation mode", [MODE_DEMO, MODE_GEMINI], key="w_mode", horizontal=True)
            st.caption("Gemini API key detected. If Gemini is unavailable, demo output is used instead."
                       if settings.gemini_configured else
                       "No GEMINI_API_KEY configured, so Gemini mode will fall back to demo output.")
            st.checkbox("Demonstrate self-correction (Demo / Mock mode only)", key="w_demo",
                        help="The first attempt is deliberately flawed so you can watch the Quality agent catch it and the agents fix it.")

        back, _mid, nxt = st.columns([1, 2.4, 1.5])
        with back:
            if step > 1:
                st.button("Back", key="wiz_back", use_container_width=True, on_click=go_step, args=(step - 1,))
        with nxt:
            if step < len(ui.WIZARD_STEPS):
                st.button("Continue", key="cta_next", type="primary", use_container_width=True, on_click=go_step, args=(step + 1,))
            else:
                st.button("Build my learning path", key="cta_build", type="primary", use_container_width=True, on_click=start_build)


if st.session_state.show_generator:
    render_wizard()


# -----------------------------
# Generation (live progress)
# -----------------------------
def run_generation(inputs: dict):
    provider = "gemini" if inputs["mode"] == MODE_GEMINI else "mock"
    subtitle = ("Gemini usually takes about 30 seconds." if provider == "gemini"
                else "Demo mode: instant, deterministic output.")
    slot = st.empty()
    states, extra, note = {"goal": ("done", "")}, [None], [""]
    slot.html(ui.progress_card(states, subtitle))

    def on_step(agent, state, detail):
        if agent == "Gemini":
            note[0] = f"Gemini was unavailable, so demo output is being used. {detail}"
        else:
            states[agent] = ("run" if state == "running" else "done", detail if state == "done" else "")
            if agent == "Regeneration":
                extra[0] = ("Regeneration", "Improving from quality feedback")
        slot.html(ui.progress_card(states, subtitle, note[0], extra[0]))
        if provider == "mock" and state == "done":
            time.sleep(0.4)  # demo output is instant; a short pause lets the agent sequence be seen

    try:
        new_result = generate_course(
            provider, inputs["topic"], inputs["audience"], inputs["duration"], inputs["difficulty"],
            inputs["goal"], on_step=on_step, inject_fault=bool(inputs["demo"]) and provider == "mock",
            weekly_hours=inputs["hours"],
        )
    except ProviderError as exc:
        slot.empty()
        st.error(f"{exc} Your answers are saved. Adjust them or try again.")
        if exc.details:
            with st.expander("Technical details"):
                st.code(exc.details)
        return
    except Exception as exc:  # last resort: never show a raw stack trace
        slot.empty()
        st.error("Something interrupted the generation. Your answers are saved. Please try again.")
        with st.expander("Technical details"):
            st.code(f"{type(exc).__name__}: {exc}")
        return

    md, pdf = build_markdown(new_result), build_pdf(new_result)   # built once per course, not per rerun
    st.session_state.exports = {"md": md, "pdf": pdf, "zip": build_course_zip(new_result, md, pdf)}
    st.session_state.result = new_result
    st.session_state.last_inputs = dict(inputs)
    st.session_state.scroll_to = "workspace"
    st.rerun()


st.html('<div id="progress" class="anchor"></div>')
consume_scroll("progress")
if st.session_state.pending:
    inputs, st.session_state.pending = st.session_state.pending, None
    run_generation(inputs)


# -----------------------------
# Results workspace
# -----------------------------
def render_results(result):
    c, v = result.curriculum, result.validation
    st.html('<div id="workspace" class="anchor" style="margin-top:56px"></div>')
    consume_scroll("workspace")
    st.html(ui.course_head(result))
    st.write("")

    exports = st.session_state.exports or {}
    a1, a2, a3, a4, a5 = st.columns([1.5, 1, 1, 1, 1])
    with a1:
        if exports:
            st.download_button("Download course (.zip)", data=exports["zip"], file_name="Course_Package.zip",
                               mime="application/zip", type="primary", use_container_width=True)
    with a2:
        if exports:
            st.download_button("Export PDF", data=exports["pdf"], file_name="Complete_Course.pdf",
                               mime="application/pdf", use_container_width=True)
    with a3:
        if exports:
            st.download_button("Markdown", data=exports["md"], file_name="Complete_Course.md",
                               mime="text/markdown", use_container_width=True)
    with a4:
        st.button("Regenerate", key="regen", use_container_width=True, on_click=regenerate,
                  help="Build a fresh version with the same answers")
    with a5:
        st.button("New course", key="new_course", use_container_width=True, on_click=reset_course)

    if result.notice:
        st.warning(result.notice)
        if result.notice_details:
            with st.expander("Technical details"):
                st.code(result.notice_details)

    st.write("")
    cols = st.columns(4)
    metrics = [("Quality check", f"{v.status} · {v.score:.0f}%"), ("Modules", len(c.modules)),
               ("Lessons", len(result.lessons.lessons)), ("Assessments", len(result.assessments.items))]
    for col, (label, value) in zip(cols, metrics):
        col.html(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>')
    st.write("")
    if v.status == "PASS":
        extra = f" after {v.attempts} attempts (self-corrected)" if v.attempts > 1 else ""
        st.success(f"Quality & Validation Agent: PASS{extra}. The package is ready for export.")
    else:
        st.error("Quality & Validation Agent: FAIL. See the Quality report tab for details.")

    tabs = st.tabs(["Curriculum", "Lessons", "Assessments", "Quality report", "Export"])

    with tabs[0]:
        st.html(ui.explain(result.request))
        st.write("")
        if c.prerequisites:
            st.markdown("**Prerequisites**")
            for item in c.prerequisites:
                st.write("•", item)
        if c.roadmap:
            st.markdown("**Roadmap**")
            st.html('<div class="timeline">' + "".join(
                f'<div class="timeline-item">{html.escape(step)}</div>' for step in c.roadmap) + "</div>")
        st.markdown("**Modules**")
        for module in c.modules:
            lessons = [l for l in result.lessons.lessons if l.module_number == module.number]
            objectives = set(module.learning_objectives)
            n_assess = sum(1 for a in result.assessments.items if a.learning_objective in objectives)
            with st.expander(f"Module {module.number:02d} · {module.title}"):
                st.html(ui.module_header(module.number, module.title, len(lessons), n_assess))
                st.write(module.summary)
                st.write("**Learning objectives**")
                for objective in module.learning_objectives:
                    st.write("•", objective)
                if lessons:
                    st.write("**Lessons**")
                    for l in lessons:
                        st.write(f"{l.module_number}.{l.lesson_number} · {l.title}")

    with tabs[1]:
        for lesson in result.lessons.lessons:
            with st.expander(f"Lesson {lesson.module_number}.{lesson.lesson_number} · {lesson.title}"):
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
            with st.expander(f"{item.type.upper()} · {item.title}"):
                st.write(item.prompt)
                correct = mcq_answer_index(item.answer, item.options) if item.options else -1
                for i, option in enumerate(item.options):
                    cls = "opt correct" if i == correct else "opt"
                    mark = " ✓" if i == correct else ""
                    st.html(f'<div class="{cls}">{chr(65 + i)}. {html.escape(option)}{mark}</div>')
                if not item.options:
                    st.write("**Answer:**", item.answer)
                st.write("**Mapped objective:**", item.learning_objective)
                if item.rubric:
                    st.write("**Rubric:**", item.rubric)

    with tabs[3]:
        st.html(ui.quality_ring(v))
        st.html(ui.check_rows(v))
        if v.attempts > 1:
            st.markdown(f"**Feedback loop:** the package passed after **{v.attempts} attempts**. Problems found and fixed automatically:")
            for issue in v.resolved_issues:
                st.write("•", issue)
        with st.expander("Raw validation report (JSON)"):
            st.json(v.model_dump())

    with tabs[4]:
        st.write("Download everything, or a single file.")
        if exports:
            st.download_button("Download Course_Package.zip", data=exports["zip"], file_name="Course_Package.zip",
                               mime="application/zip", type="primary", use_container_width=True, key="dl_zip_tab")
        st.caption("The ZIP contains: Complete_Course (PDF + MD), Lessons.md, Answer_Key.md, Curriculum.json, "
                   "Assessments.json and Validation_Report.json. AI-generated content should be reviewed by an instructor before classroom use.")


if result:
    render_results(result)


# -----------------------------
# Narrative sections
# -----------------------------
st.html(ui.process_section())
consume_scroll("how")
st.html(ui.why_section())
st.html(ui.bento_section())
st.html(ui.quality_section())
st.html(ui.cta_band())
_, mid, _ = st.columns([1.2, 1, 1.2])
with mid:
    st.button("Build my learning path", key="cta_final", type="primary", use_container_width=True, on_click=open_wizard)
st.html(ui.footer())
