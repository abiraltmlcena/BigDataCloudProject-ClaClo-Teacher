from pydantic import BaseModel
from typing import List

class Class(BaseModel):
    module_name: str
    student: List[str] = []  # List of students IDs