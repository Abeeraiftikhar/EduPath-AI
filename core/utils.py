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


_SMALL_WORDS = {"a", "an", "and", "as", "at", "for", "in", "of", "on", "or", "the", "to", "with", "vs"}


def clean_topic(raw: str) -> str:
    """Tidy a typed topic: collapse whitespace and capitalise it ('python' -> 'Python').

    Words that already contain capitals (SQL, iOS, NLP) are left alone, so acronyms survive.
    """
    words = (raw or "").split()
    cleaned = []
    for i, word in enumerate(words):
        if any(c.isupper() for c in word):
            cleaned.append(word)
        elif i > 0 and word.lower() in _SMALL_WORDS:
            cleaned.append(word.lower())
        else:
            cleaned.append(word[:1].upper() + word[1:])
    return " ".join(cleaned)


def validate_topic(topic: str):
    """Return an error message for an unusable topic, or None. One word is perfectly fine."""
    if len(topic) < 2:
        return "Please enter a topic (even a single word such as 'Python' works)."
    if not any(c.isalpha() for c in topic):
        return "The topic needs at least one letter."
    if len(topic) > 80:
        return "Please keep the topic under 80 characters."
    return None


def snap_objectives(assessment_items, curriculum, cutoff: float = 0.6):
    """LLMs often paraphrase a learning objective. Snap each item to the closest real one so the
    mapping stays exact. Returns the number of items that were corrected."""
    from difflib import get_close_matches

    objectives = [o for m in curriculum.modules for o in m.learning_objectives]
    fixed = 0
    for item in assessment_items:
        if item.learning_objective not in objectives:
            match = get_close_matches(item.learning_objective, objectives, n=1, cutoff=cutoff)
            if match:
                item.learning_objective, fixed = match[0], fixed + 1
    return fixed


def uncovered_objectives(curriculum, assessment_items):
    """Learning objectives that no assessment item is mapped to (in curriculum order)."""
    covered = {i.learning_objective for i in assessment_items}
    return [o for m in curriculum.modules for o in m.learning_objectives if o not in covered]
