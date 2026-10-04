import re


def parse_weeks(duration: str, default: int = 4) -> int:
    """'4 Weeks' -> 4. Falls back to `default` when no number is present."""
    match = re.search(r"\d+", duration or "")
    return max(1, int(match.group())) if match else default


def mcq_answer_index(answer: str, options: list) -> int:
    """Index of the correct option for an answer given as a letter ('B') or as the option text; -1 if invalid."""
    cleaned = (answer or "").strip()
    if len(cleaned) == 1 and cleaned.upper().isalpha():
        index = ord(cleaned.upper()) - 65
        return index if 0 <= index < len(options) else -1
    for i, option in enumerate(options):
        if option.strip().lower() == cleaned.lower():
            return i
    return -1
