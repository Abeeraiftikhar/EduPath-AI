"""UI tests: pure HTML builders plus the wizard flow driven through Streamlit's AppTest harness."""
import pytest
from streamlit.testing.v1 import AppTest

from core.orchestrator import CourseOrchestrator
from ui import sections as ui

APP = "app.py"


def course():
    return CourseOrchestrator("mock").generate("Python", "Undergraduate students", "4 Weeks", "Beginner",
                                               "Build practical, job-ready skills", weekly_hours="5-8 hrs/week")


# ------------------------------------------------------------- HTML builders
def test_user_text_is_escaped_everywhere():
    evil = '<script>alert(1)</script>"&'
    result = CourseOrchestrator("mock").generate(evil, "PhD researchers", "2 Weeks", "Advanced", "Build practical, job-ready skills")
    for fragment in (ui.preview_card(result), ui.course_head(result), ui.explain(result.request),
                     ui.quality_ring(result.validation), ui.check_rows(result.validation)):
        assert "<script>" not in fragment
    assert "&lt;script&gt;" in ui.course_head(result)


def test_preview_shows_samples_then_real_course():
    assert ui.preview_card(None).count('class="slide"') == len(ui.SAMPLE_COURSES) == 4
    real = ui.preview_card(course())
    assert "Generated" in real and "slide" not in real


def test_sample_course_counts_match_demo_output():
    """The marketing samples must not promise more than Demo mode really produces."""
    for topic, audience, duration, level, objectives, lessons, modules in ui.SAMPLE_COURSES:
        r = CourseOrchestrator("mock").generate(topic, audience, duration, level, "Build practical, job-ready skills")
        assert len(r.curriculum.modules) == len(modules)
        assert sum(len(m.learning_objectives) for m in r.curriculum.modules) == objectives
        assert len(r.lessons.lessons) == lessons


def test_quality_checklist_copy_matches_the_validator():
    assert len(ui.QUALITY_CHECKS) == len(course().validation.checks) == 10


def test_pips_mark_progress():
    html = ui.pips(3)
    assert html.count("pip done") == 2 and html.count("pip on") == 1 and html.count("pip-line done") == 2


def test_progress_card_percentage():
    states = {"goal": ("done", ""), "Curriculum Architect": ("done", "4 modules"), "Content Creator": ("run", "")}
    assert "width:40%" in ui.progress_card(states)


def test_icons_stylesheet_covers_every_icon_used():
    import re
    from pathlib import Path
    css = Path("assets/icons.css").read_text(encoding="utf-8")
    used = set(re.findall(r'ic-([a-z]+)', "".join([
        ui.brand(), ui.trust_row(), ui.process_section(), ui.why_section(), ui.bento_section(), ui.quality_section(),
        ui.course_head(course()), ui.explain(course().request)])))
    for name in used:
        assert f".ic-{name}" in css, name


# ------------------------------------------------------------------ app flow
def fresh():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    return at


def click(at, key):
    at.button(key=key).click().run()
    assert not at.exception, at.exception
    return at


def test_home_renders_without_errors_in_both_themes():
    at = fresh()
    assert at.session_state.dark is True            # dark is the default
    click(at, "nav_theme")
    assert at.session_state.dark is False


def test_open_wizard_validates_topic_then_advances():
    at = fresh()
    click(at, "cta_hero")
    assert at.session_state.wiz_step == 1
    click(at, "cta_next")                            # empty topic: blocked with a message
    assert at.session_state.wiz_step == 1 and at.error
    at.text_input(key="w_topic").set_value("python").run()
    click(at, "cta_next")
    assert at.session_state.wiz_step == 2 and at.session_state.wiz["topic"] == "Python"


def test_sample_goes_to_review_and_builds_a_course():
    at = fresh()
    click(at, "hero_sample")
    assert at.session_state.wiz_step == 5 and at.session_state.wiz["topic"] == "Python for Bioinformatics"
    at.radio(key="w_mode").set_value("Demo / Mock — no API key").run()
    click(at, "cta_build")
    result = at.session_state.result
    assert result and result.validation.status == "PASS" and result.request.weekly_hours == "5-8 hrs/week"
    assert at.session_state.exports and set(at.session_state.exports) == {"md", "pdf", "zip"}


def test_regenerate_and_new_course():
    at = fresh()
    click(at, "hero_sample")
    at.radio(key="w_mode").set_value("Demo / Mock — no API key").run()
    click(at, "cta_build")
    first = at.session_state.result
    click(at, "regen")
    assert at.session_state.result is not first and at.session_state.result.request == first.request
    click(at, "new_course")
    assert at.session_state.result is None and at.session_state.wiz_step == 1 and at.session_state.wiz["topic"] == ""


def test_logo_assets_exist_and_have_sane_shape():
    from pathlib import Path
    from PIL import Image
    brand = Path("assets/brand")
    for name in ("Logo.png", "logo_full.png", "logo_full_dark.png", "logo_mark.png", "logo_mark_dark.png"):
        img = Image.open(brand / name)
        assert img.mode == "RGBA" and img.getchannel("A").getextrema()[0] == 0, name   # transparent background kept
    mark = Image.open(brand / "logo_mark.png")
    assert 1.0 < mark.width / mark.height < 2.0 and mark.height >= 100              # crisp enough for retina nav use
    assert Image.open("assets/favicon.png").size == (128, 128)


def test_brand_uses_logo_image_not_text_icon():
    html = ui.brand()
    assert 'class="logo"' in html and "ic-sparkles" not in html and "EduPath-AI" in html
