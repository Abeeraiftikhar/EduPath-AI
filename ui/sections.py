"""Static HTML for the EduPath-AI interface. Pure functions: easy to test, no Streamlit state.

Everything user-supplied goes through `esc()`. Icons are CSS masks (`<i class="ic ic-x">`), see make_icons.py.
"""
import html

# Real sample outputs (counts match what Demo mode really produces for those settings).
SAMPLE_COURSES = [
    # topic, audience, duration, level, objectives, lessons, modules
    ("Python for Bioinformatics", "Undergraduate students", "4 Weeks", "Beginner", 8, 8,
     ["Foundations of Python", "Core Concepts and Tools", "Python in Practice", "Applied Project"]),
    ("Digital Marketing Fundamentals", "Small business owners", "6 Weeks", "Beginner", 10, 10,
     ["Marketing Foundations", "Audiences and Channels", "Content and Campaigns", "Measuring Results", "Capstone Campaign"]),
    ("Machine Learning with Scikit-learn", "Working professionals", "8 Weeks", "Intermediate", 12, 12,
     ["Foundations", "Data Preparation", "Model Training", "Evaluation", "Deployment", "Capstone Project"]),
    ("Scientific Writing for Researchers", "PhD researchers", "2 Weeks", "Advanced", 6, 6,
     ["Structure and Argument", "Writing in Practice", "Capstone Manuscript"]),
]

QUALITY_CHECKS = [
    "Modules and learning objectives are present",
    "Module count fits the course duration",
    "Every module has lesson content",
    "Every lesson has notes, examples and exercises",
    "Lesson titles are unique",
    "Assessments include answers",
    "Assessments map to real learning objectives",
    "Every learning objective is assessed",
    "Multiple-choice answers are valid",
    "Assignments and projects have rubrics",
]


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def ic(name: str) -> str:
    return f'<i class="ic ic-{name}"></i>'


# ------------------------------------------------------------------ navigation
def brand() -> str:
    return '<div class="brand"><span class="logo" role="img" aria-label="EduPath-AI logo"></span><div class="brand-name">EduPath-AI</div></div>'


# ------------------------------------------------------------------------ hero
def hero_copy() -> str:
    return (
        '<div class="hero">'
        '<div class="eyebrow">AI-powered personal learning</div>'
        '<h1 class="display">Build a learning path that <span class="grad">actually fits you.</span></h1>'
        '<div class="lead">Tell EduPath-AI what you want to learn, where you are starting from and how much time you have. '
        'Specialized AI agents build the curriculum, lessons and assessments around your goals.</div>'
        '</div>'
    )


def trust_row() -> str:
    items = ["Personalized curriculum", "Multi-agent generation", "Quality validation", "Downloadable course"]
    return '<div class="trust">' + "".join(f'<span>{ic("check")}{t}</span>' for t in items) + "</div>"


def _path_list(modules) -> str:
    return '<ul class="path">' + "".join(f"<li><i>{n}</i>{esc(m)}</li>" for n, m in enumerate(modules, 1)) + "</ul>"


def _stats(objectives, modules, lessons, status_html) -> str:
    cells = [(objectives, "Objectives"), (modules, "Modules"), (lessons, "Lessons")]
    body = "".join(f'<div class="stat"><b>{n}</b><span>{label}</span></div>' for n, label in cells)
    return f'<div class="stats">{body}<div class="stat">{status_html}<span>Quality check</span></div></div>'


def preview_card(result=None) -> str:
    """Hero card: rotating sample learning paths, or the learner's real course once generated."""
    if result:
        c, r, v = result.curriculum, result.request, result.validation
        objectives = sum(len(m.learning_objectives) for m in c.modules)
        status = f'<b class="{"pass" if v.status == "PASS" else "fail"}">{v.status}</b>'
        body = (
            '<div class="preview-head">'
            f'<div class="preview-title">{esc(c.title)}</div><span class="badge badge-done">Generated</span></div>'
            f'<div class="preview-sub">{esc(r.audience)} · {esc(r.difficulty)} · {esc(r.duration)}</div>'
            + _stats(objectives, len(c.modules), len(result.lessons.lessons), status)
            + _path_list([m.title for m in c.modules])
        )
        top = '<div class="preview-top"><span class="label">Your learning path</span></div>'
        note = ""
    else:
        slides = ""
        for topic, audience, duration, level, obj, lessons, modules in SAMPLE_COURSES:
            slides += (
                '<div class="slide"><div class="preview-head">'
                f'<div class="preview-title">{esc(topic)}</div><span class="badge">Sample</span></div>'
                f'<div class="preview-sub">{esc(audience)} · {esc(level)} · {esc(duration)}</div>'
                + _stats(obj, len(modules), lessons, '<b class="pass">PASS</b>')
                + _path_list(modules) + "</div>"
            )
        body = f'<div class="rotor">{slides}</div>'
        top = ('<div class="preview-top"><span class="label">AI learning path</span>'
               f'<span class="dots">{"<i></i>" * len(SAMPLE_COURSES)}</span></div>')
        note = '<div class="sample-note">Sample learning paths. Build your own in under a minute.</div>'
    return f'<div class="float"><div class="preview">{top}{body}{note}</div></div>'


# ---------------------------------------------------------------- narrative
def process_section() -> str:
    nodes = [
        ("compass", "c-indigo", "01", "Your goal", "You describe what to learn, your level and your available time."),
        ("route", "c-indigo", "02", "Curriculum Architect", "Maps prerequisites, objectives, modules and a realistic roadmap."),
        ("book", "c-violet", "03", "Content Creator", "Writes lesson notes, examples, exercises and case studies."),
        ("target", "c-blue", "04", "Assessment Agent", "Builds quizzes, assignments, answer keys and rubrics."),
        ("shield", "c-green", "05", "Quality Agent", "Runs ten checks and sends any problem back to be fixed."),
    ]
    cards = "".join(
        f'<div class="node {cls} reveal d{i}"><div class="orb">{ic(icon)}</div><div class="num">{num}</div>'
        f"<h4>{title}</h4><p>{text}</p></div>"
        for i, (icon, cls, num, title, text) in enumerate(nodes, 1)
    )
    return (
        '<div class="section" id="how">'
        '<div class="section-head reveal"><div class="eyebrow">How it works</div>'
        '<h2 class="h2">From goal to complete <span class="grad">learning path</span></h2>'
        '<div class="copy">Specialized AI agents work in sequence, each handing structured output to the next, '
        'and a quality layer validates the result before you see it.</div></div>'
        f'<div class="pipe"><div class="pipe-line"></div>{cards}</div></div>'
    )


def why_section() -> str:
    items = [
        ("user", "c-indigo", "Personalized by design", "Courses adapt to you.",
         ["Your current level", "Your goal and audience", "Your time frame and weekly hours"]),
        ("layers", "c-violet", "Agent-powered", "Each agent has one job.",
         ["Curriculum design", "Lesson content", "Assessment and quality control"]),
        ("shield", "c-green", "Quality checked", "Nothing ships unchecked.",
         ["Ten automated checks", "Problems are fixed automatically", "A clear, explainable report"]),
        ("package", "c-blue", "Ready to use", "A package, not a chat log.",
         ["Structured curriculum", "PDF, Markdown and JSON", "Answer key included"]),
    ]
    cards = "".join(
        f'<div class="card {cls} reveal d{i}"><div class="ico">{ic(icon)}</div><div class="h3">{title}</div>'
        f'<div class="copy">{sub}</div><ul>' + "".join(f"<li>{ic('check')}{b}</li>" for b in bullets) + "</ul></div>"
        for i, (icon, cls, title, sub, bullets) in enumerate(items, 1)
    )
    return (
        '<div class="section"><div class="section-head reveal"><div class="eyebrow">Why EduPath-AI</div>'
        '<h2 class="h2">Not another AI chatbot.<br>A complete <span class="grad">learning system.</span></h2></div>'
        f'<div class="grid grid-4">{cards}</div></div>'
    )


def bento_section() -> str:
    def card(span, cls, icon, title, bullets, extra=""):
        lis = "".join(f"<li>{ic('check')}{b}</li>" for b in bullets)
        return (f'<div class="card {cls} {span} reveal"><div class="ico">{ic(icon)}</div><div class="h3">{title}</div>'
                f"<ul>{lis}</ul>{extra}</div>")

    path = '<div class="mini-path"><span class="on">Foundations</span><span>Core practice</span><span>Applied project</span><span>Capstone</span></div>'
    files = '<div class="mini-path"><span class="on">Course PDF</span><span>Complete_Course.md</span><span>Lessons.md</span><span>Answer_Key.md</span><span>Curriculum.json</span></div>'
    return (
        '<div class="section"><div class="section-head reveal"><div class="eyebrow">What you get</div>'
        '<h2 class="h2">Your complete <span class="grad">course</span>, in one package</h2></div>'
        '<div class="bento">'
        + card("b-wide", "c-indigo", "route", "Learning roadmap", ["Prerequisites", "Measurable objectives", "Modules in sequence", "A week-by-week timeline"], path)
        + card("b-sm", "c-violet", "book", "Lesson content", ["Notes", "Examples", "Exercises", "Case studies"])
        + card("b-sm", "c-blue", "target", "Assessments", ["Quizzes and MCQs", "Assignments", "Answer keys", "Rubrics"])
        + card("b-wide", "c-green", "package", "Course package", ["Structured, downloadable output", "Ready for a classroom or self-study"], files)
        + "</div></div>"
    )


def quality_section() -> str:
    rows = "".join(f'<div class="check-row"><span class="mark">{ic("check")}</span><div>{c}</div></div>' for c in QUALITY_CHECKS)
    return (
        '<div class="section"><div class="split">'
        '<div class="reveal"><div class="eyebrow">Quality and trust</div>'
        '<h2 class="h2">Every course is <span class="grad">checked</span> before you see it.</h2>'
        '<div class="copy" style="margin-top:18px;font-size:17px">A dedicated Quality agent validates structure, alignment and completeness. '
        'If something fails, the problem is sent back to the right agent to be fixed, and the report shows exactly what was checked and what changed.</div>'
        '<div class="copy" style="margin-top:14px">AI-generated material should still be reviewed by an instructor before classroom use.</div></div>'
        '<div class="report reveal d2"><div class="label" style="margin-bottom:14px">Quality report · 10 checks on every course</div>'
        f"{rows}</div></div></div>"
    )


def cta_band() -> str:
    return (
        '<div class="cta-band reveal"><div class="eyebrow">Ready when you are</div>'
        '<h2 class="h2">Your next skill deserves<br>a <span class="grad">better roadmap.</span></h2>'
        '<div class="copy">Tell us where you want to go. EduPath-AI will build the path to get you there.</div></div>'
    )


def footer() -> str:
    return (
        '<div class="site-footer">'
        f'<div>{brand()}<p style="margin-top:14px;max-width:340px">AI-powered personalized learning paths, built by specialized agents and checked by a quality layer.</p></div>'
        '<div><h5>Product</h5><ul><li>Discover</li><li>How it works</li><li>Build a learning path</li></ul></div>'
        '<div><h5>Built with</h5><ul><li>Streamlit</li><li>Pydantic</li><li>Google Gemini</li></ul></div>'
        '<div class="legal"><span>© 2026 EduPath-AI</span><span>Designed for learners, researchers and professionals.</span></div>'
        '</div>'
    )


# ---------------------------------------------------------------------- wizard
WIZARD_STEPS = ["Topic", "Level", "Goal", "Time", "Review"]


def pips(step: int) -> str:
    out = []
    for i, name in enumerate(WIZARD_STEPS, 1):
        state = "done" if i < step else "on" if i == step else ""
        mark = ic("check") if i < step else str(i)
        out.append(f'<div class="pip {state}"><span class="pm">{mark}</span><span class="pl">{name}</span></div>')
        if i < len(WIZARD_STEPS):
            out.append(f'<div class="pip-line {"done" if i < step else ""}"></div>')
    return f'<div class="pips" role="list" aria-label="Progress">{"".join(out)}</div>'


def step_heading(question: str, help_text: str) -> str:
    return f'<h3 class="step-q">{esc(question)}</h3><div class="step-help">{esc(help_text)}</div>'


def summary(items) -> str:
    return '<div class="summary">' + "".join(f"<div><span>{esc(k)}</span><b>{esc(v)}</b></div>" for k, v in items) + "</div>"


# ------------------------------------------------------------------ generation
GEN_ROWS = [
    ("goal", "Understanding your goal"),
    ("Curriculum Architect", "Designing the curriculum"),
    ("Content Creator", "Creating lesson content"),
    ("Assessment Agent", "Generating assessments"),
    ("Quality & Validation Agent", "Running quality checks"),
]


def progress_card(states: dict, subtitle: str = "", note: str = "", extra_row=None) -> str:
    """`states` maps an agent key to (state, detail) where state is 'run' or 'done'."""
    rows = list(GEN_ROWS) + ([extra_row] if extra_row else [])
    done = sum(1 for k, _ in rows if states.get(k, ("", ""))[0] == "done")
    pct = int(100 * done / len(rows))
    body = ""
    for key, label in rows:
        state, detail = states.get(key, ("", ""))
        mark = ic("check") if state == "done" else ""
        small = f"<small>{esc(detail)}</small>" if detail else ""
        body += f'<div class="gen-row {state}"><span class="dot">{mark}</span><span class="name">{esc(label)}</span>{small}</div>'
    note_html = f'<div class="gen-note">{esc(note)}</div>' if note else ""
    return (
        '<div class="gen"><div class="gen-title">Building your learning path</div>'
        f'<div class="gen-sub">{esc(subtitle)}</div>'
        f'<div class="gen-bar"><i style="width:{pct}%"></i></div>{body}{note_html}</div>'
    )


# --------------------------------------------------------------------- results
def course_head(result) -> str:
    c, r = result.curriculum, result.request
    chips = [("cap", r.difficulty), ("clock", r.duration), ("user", r.audience), ("target", r.learning_goal)]
    if getattr(r, "weekly_hours", None):
        chips.append(("clock", r.weekly_hours))
    chips.append(("sparkles", "Gemini" if result.provider_used == "gemini" else "Demo mode"))
    chip_html = "".join(f'<span class="chip">{ic(i)}{esc(t)}</span>' for i, t in chips)
    return (
        '<div class="course-head"><div class="label" style="margin-bottom:10px">Your learning path</div>'
        f'<h2 class="h2">{esc(c.title)}</h2><div class="copy" style="margin-top:14px;font-size:16px">{esc(c.description)}</div>'
        f'<div class="chips">{chip_html}</div></div>'
    )


def module_header(number: int, title: str, lessons: int, assessments: int) -> str:
    return (f'<div class="mod-head"><span class="mod-kicker">MODULE {number:02d}</span>'
            f'<span class="mod-title">{esc(title)}</span>'
            f'<span class="mod-meta">{lessons} lessons · {assessments} assessments</span></div>')


def quality_ring(validation) -> str:
    color = "var(--success)" if validation.status == "PASS" else "var(--danger)"
    passed = sum(c.passed for c in validation.checks)
    return (
        f'<div class="ring-wrap"><div class="ring" style="--p:{validation.score:.0f};--ring:{color}">'
        f'<div><b>{validation.score:.0f}</b><small>of 100</small></div></div>'
        f'<div><span class="badge {"badge-done" if validation.status == "PASS" else ""}">{validation.status}</span>'
        f'<div class="h3" style="margin-top:10px">{passed} of {len(validation.checks)} checks passed</div>'
        f'<div class="copy">Computed from the automated checks below, not estimated.</div></div></div>'
    )


def check_rows(validation) -> str:
    out = ""
    for k in validation.checks:
        detail = f'<div class="check-detail">{esc(k.detail)}</div>' if k.detail else ""
        mark = ic("check") if k.passed else "✗"
        out += f'<div class="check-row {"" if k.passed else "bad"}"><span class="mark">{mark}</span><div>{esc(k.name)}{detail}</div></div>'
    return out


def explain(request) -> str:
    items = [("Topic", request.topic), ("Your level", request.difficulty), ("Audience", request.audience),
             ("Your goal", request.learning_goal), ("Time frame", request.duration)]
    if getattr(request, "weekly_hours", None):
        items.append(("Weekly time", request.weekly_hours))
    lis = "".join(f"<li><b>{esc(k)}:</b> {esc(v)}</li>" for k, v in items)
    return (f'<div class="explain"><div class="h3">{ic("lightbulb")} Why this path was shaped this way</div>'
            f'<div class="copy" style="margin-top:6px">The curriculum, lesson depth and number of modules were adapted to:</div><ul>{lis}</ul></div>')
