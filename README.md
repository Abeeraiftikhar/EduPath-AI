# EduPath-AI

## Autonomous Multi-Agent Course & Training Curriculum Generator

EduPath-AI transforms a simple learning request into a structured, validated and downloadable course package using specialized agents.

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/UI-Streamlit-red) ![License](https://img.shields.io/badge/license-see%20LICENSE-green)

> **Live demo:** _add your Streamlit Community Cloud URL here after deploying_ · **Sample output:** [examples/Sample_Course_Package.zip](examples/Sample_Course_Package.zip)

## Highlights

- **Input-aware generation** - module count, roadmap and objective wording adapt to duration, difficulty and topic (even in demo mode).
- **10-check Quality agent** with an explainable score, and a **real feedback loop** that sends issues back to only the failing agent.
- **Live agent progress**, per-check validation checklist, roadmap timeline, highlighted MCQ answers.
- **Resilient Gemini mode**: retries that honor rate-limit hints, model fallbacks, friendly errors, automatic fallback to demo output.
- **Dark mode**, sober CSS animations (respecting reduced-motion) and a rotating sample-course preview.
- **Complete exports**: PDF (with page numbers), Markdown, `Lessons.md`, `Answer_Key.md`, JSON, ZIP.

### Input
- Topic
- Target audience
- Duration
- Difficulty
- Learning goal

### Output
- Curriculum
- Lessons
- Quizzes / MCQs
- Assignments
- Answer keys
- Rubrics
- Validation report
- PDF / JSON / Markdown / ZIP exports

## Architecture

```text
Streamlit UI
    |
    v
Orchestrator
    |
    +--> Curriculum Architect
    |
    +--> Content Creator
    |
    +--> Assessment Agent
    |
    +--> Quality & Validation Agent
                |
          FAIL -> regeneration
          PASS -> export
```

## Technology

- Frontend: Streamlit
- Agent architecture: four specialized agents with an orchestrator
- LLM: Gemini free tier (optional)
- Schemas: Pydantic
- PDF: ReportLab
- Hosting target: Streamlit Community Cloud
- Repository target: GitHub
- Demo mode: deterministic mock provider, no API key required

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt      # use requirements-dev.txt to also get pytest
streamlit run app.py
```

The default Demo / Mock mode works without a key.

### Gemini mode

Copy `.env.example` to `.env` and add:

```text
GEMINI_API_KEY=your_key_here
```

Never commit `.env` or API keys.

## Test

```bash
pytest -q
```

## Deployment

For Streamlit Community Cloud:
1. Push this repository to GitHub.
2. Select `app.py` as the main file.
3. Add `GEMINI_API_KEY` under App Settings → Secrets if Gemini mode is needed.
4. Keep the repository free of API keys.

## Demo scenario

Use **Try a sample profile**, pick Duration **4 Weeks**, tick **Demonstrate self-correction**, and generate.
Watch the Quality agent fail the first attempt and the agents fix it, then inspect the Validation tab and
download the ZIP. The full walkthrough is in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

## Project structure

```text
EduPath-AI/
├── app.py                      # Streamlit UI
├── agents/                     # curriculum, content, assessment, quality (+ base.py feedback prompt)
├── core/                       # schemas, orchestrator, providers, exporter, utils, config
├── tests/test_pipeline.py      # 23 tests: pipeline, quality checks, feedback loop, exports, Gemini handling
├── examples/                   # pre-generated sample package
├── docs/                       # architecture, user guide, demo script, scope, handoff
├── requirements.txt / requirements-dev.txt
└── .env.example
```

## Limitations & roadmap

- Gemini output quality depends on the model; the Quality agent checks structure and alignment, not factual accuracy.
  AI-generated content should be reviewed by an instructor before use.
- The PDF uses a standard Latin font; non-Latin scripts need an embedded font.
- Future extensions: LMS integration, multilingual support, progress tracking, local LLM mode, instructor dashboards.

## Scope discipline

The project intentionally does not require accounts, email delivery, or user-supplied API keys. It is designed for zero-cost hackathon execution using free-tier APIs and open-source technologies.
