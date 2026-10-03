# EduPath-AI

## Autonomous Multi-Agent Course & Training Curriculum Generator

EduPath-AI transforms a simple learning request into a structured, validated and downloadable course package using specialized agents.

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

pip install -r requirements.txt
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

Use:
- Topic: Python for Bioinformatics
- Audience: Undergraduate
- Duration: 4 Weeks
- Difficulty: Beginner
- Goal: Build practical Python skills for biological sequence analysis.

Generate the package, inspect the validation result, then download the ZIP.

## Project structure

```text
EduPath-AI/
├── app.py
├── agents/
│   ├── curriculum_agent.py
│   ├── content_agent.py
│   ├── assessment_agent.py
│   └── quality_agent.py
├── core/
│   ├── config.py
│   ├── schemas.py
│   ├── llm_provider.py
│   ├── mock_provider.py
│   ├── orchestrator.py
│   └── exporter.py
├── tests/
│   └── test_pipeline.py
├── .streamlit/config.toml
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Scope discipline

The project intentionally does not make accounts, email delivery, or user-supplied API keys mandatory. It is designed for zero-cost hackathon execution using free-tier APIs and open-source technologies.

Future extensions can include LMS integration, student progress tracking, personalized paths, multilingual support, local LLM mode, instructor dashboards and analytics.
