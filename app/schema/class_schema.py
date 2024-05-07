from typing import List
from .student_schema import individual_serial as student_individual_serial

def class_individual_serial(classe) -> dict:
    return {
        "class_id": str(classe["_id"]),
        "module_name": classe["module_name"],
        "student": [student_individual_serial(student) for student in classe["student"]]
    }

def class_list(classes) -> list:
    return [class_individual_serial(classe) for classe in classes]


