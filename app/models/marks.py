from pydantic import BaseModel
from .answers import Answer
from .exercises import Exercise
from .students import Student

class Mark(BaseModel):
    answer_id: Answer  # Foreign key referencing the Answer model
    exercise_id: Exercise  # Foreign key referencing the Exercise model
    student_id: Student  # Foreign key referencing the Student model
    mark_number: float
    feedback: str