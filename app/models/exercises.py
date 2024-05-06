from fastapi import FastAPI, UploadFile
from pydantic import BaseModel, Field
from datetime import datetime
from .classes import Class

class Exercise(BaseModel):
    topic: str
    exercise_file: UploadFile
    class_id: Class  # Foreign key referencing the Class model
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    submission_date: datetime
