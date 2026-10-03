# EduPath-AI Architecture

## Pipeline

User input is validated into `CourseRequest`.

`CourseOrchestrator` runs:

1. Curriculum Agent
2. Content Agent
3. Assessment Agent
4. Quality Agent

The Quality Agent checks:
- module presence
- learning objectives
- lesson coverage
- assessment answers
- assessment-to-objective mapping
- duplicate lesson titles

A failed validation can trigger one controlled regeneration pass when Gemini mode is active.

## Separation of concerns

- `agents/` contains agent responsibilities.
- `core/schemas.py` defines structured contracts.
- `core/llm_provider.py` isolates Gemini.
- `core/mock_provider.py` enables development without external services.
- `core/exporter.py` handles downloadable artifacts.
- `app.py` contains the presentation layer.
