def feedback_block(feedback) -> str:
    """Prompt section telling the model what the validator rejected on the previous attempt."""
    if not feedback:
        return ""
    problems = "\n".join(f"- {f}" for f in feedback)
    return f"\nA quality review of your previous attempt found these problems. Fix all of them:\n{problems}\n"
