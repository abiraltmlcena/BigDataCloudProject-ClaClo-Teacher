from pydantic import BaseModel, Field
from datetime import datetime
from .students import Student
from .exercises import Exercise
from .classes import Class

class Answer(BaseModel):
    exercise_id: Exercise  # Foreign key referencing the Exercise model
    class_id: Class  # Foreign key referencing the Class model
    student_id: Student  # Foreign key referencing the Student model
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    answer_data: UploadFIle  # Binary datatype for the submitted answer conten
