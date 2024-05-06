from fastapi import FastAPI, UploadFile
from pydantic import BaseModel, Field
from datetime import datetime
from .classes import Class

class StudyMaterial(BaseModel):
    class_id: Class  # Foreign key referencing the Class model
    topic: str
    material: UploadFile
    upload_date: datetime =  datetime.utcnow()