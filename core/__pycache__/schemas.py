from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class CourseRequest(BaseModel):
    topic: str
    audience: str
    duration: str
    difficulty: str
    learning_goal: str

class Module(BaseModel):
    number: int
    title: str
    summary: str
    prerequisites: List[str] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)

class Curriculum(BaseModel):
    title: str
    description: str
    prerequisites: List[str] = Field(default_factory=list)
    modules: List[Module]
    roadmap: List[str] = Field(default_factory=list)

class Lesson(BaseModel):
    module_number: int
    lesson_number: int
    title: str
    notes: str
    examples: List[str] = Field(default_factory=list)
    exercises: List[str] = Field(default_factory=list)
    case_study: Optional[str] = None
    learning_objectives: List[str] = Field(default_factory=list)

class LessonPackage(BaseModel):
    lessons: List[Lesson]

class AssessmentItem(BaseModel):
    type: Literal["mcq", "quiz", "assignment", "project"]
    title: str
    prompt: str
    options: List[str] = Field(default_factory=list)
    answer: str
    learning_objective: str
    rubric: Optional[str] = None

class AssessmentPackage(BaseModel):
    items: List[AssessmentItem]

class ValidationReport(BaseModel):
    status: Literal["PASS", "FAIL"]
    score: float = 0.0
    issues: List[str] = Field(default_factory=list)
    feedback: List[str] = Field(default_factory=list)
    checked_items: List[str] = Field(default_factory=list)

class CoursePackage(BaseModel):
    request: CourseRequest
    curriculum: Curriculum
    lessons: LessonPackage
    assessments: AssessmentPackage
    validation: ValidationReport
