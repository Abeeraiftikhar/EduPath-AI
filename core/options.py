"""Fixed choices for the generator form (no free typing except the topic)."""

AUDIENCES = [
    "School students (Grades 6-10)",
    "High-school students",
    "Undergraduate students",
    "Graduate / Master's students",
    "PhD researchers",
    "Early-career professionals",
    "Working professionals",
    "Managers and team leads",
    "Small business owners",
    "Teachers and trainers",
    "Career changers",
    "Self-learners and hobbyists",
]

LEARNING_GOALS = [
    "Build practical, job-ready skills",
    "Understand the core fundamentals",
    "Prepare for an exam or certification",
    "Complete a hands-on portfolio project",
    "Prepare for academic study or research",
    "Switch careers or upskill for a promotion",
    "Teach or train others on this topic",
]

DURATIONS = ["1 Week", "2 Weeks", "4 Weeks", "6 Weeks", "8 Weeks", "12 Weeks"]
DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]

TOPIC_EXAMPLES = ["Python", "Digital Marketing", "Photosynthesis", "Machine Learning", "Public Speaking", "Personal Finance"]

# Prefilled by "Try a sample profile".
SAMPLE = {
    "topic": "Python for Bioinformatics",
    "audience": "Undergraduate students",
    "duration": "4 Weeks",
    "difficulty": "Intermediate",
    "goal": "Build practical, job-ready skills",
}
