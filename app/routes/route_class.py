from fastapi import APIRouter, Body, HTTPException, Path, Depends
from schema.class_schema import class_list
from config.database import db
from auth.auth_bearer import jwtBearer
from bson import ObjectId
from typing import List

classe = APIRouter()

student_collection = db["student_collection"]
class_collection = db["class_collection"]

# Get all class from the database
@classe.get("/class", dependencies=[Depends(jwtBearer())], tags=["class"])
async def get_class():
    classes = class_list(class_collection.find())
    return classes


# Get all students by class ID
@classe.get("/classes/{class_id}/students", dependencies=[Depends(jwtBearer())], tags=["class"])
async def get_students_by_class_id(class_id: str):
    # Check if class exists
    class_doc = class_collection.find_one({"_id": ObjectId(class_id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    # Retrieve students for the given class ID
    students = class_doc.get("student", [])
    student_list = []
    for student in students:
        student_details = {
            "student_id": str(student["_id"]),
            "name": student["name"],
            "email": student["email"]
        }
        student_list.append(student_details)
    
    return student_list


# Create a new class with student IDs
@classe.post("/classes/", tags=["Admin"])
async def create_class(module_name: str, students: List[str]):
    try:
        # Get student details for the provided student IDs
        student_details = []
        for student_id in students:
            student = student_collection.find_one(
                {"_id": ObjectId(student_id)},
                {"student_id": 1, "name": 1, "email": 1}  # Include student_id, name, and email
            )
            if student:
                student_details.append(student)
            else:
                raise HTTPException(status_code=404, detail=f"Student with ID {student_id} not found")

        # Create a new class
        new_class = {
            "module_name": module_name,
            "student": student_details
        }
        db.class_collection.insert_one(new_class)
        # class_id = str(inserted_class.inserted_id)

        return {"message": "Class created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create class")



#  Add students to the class
@classe.post("/classes/{class_id}/students/{student_id}", dependencies=[Depends(jwtBearer())], tags=["class"])
async def add_student_to_class(
    class_id: str = Path(..., title="The ID of the class"),
    student_id: str = Path(..., title="The ID of the student")
):
    # Check if class exists
    class_doc = class_collection.find_one({"_id": ObjectId(class_id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    # Check if student exists
    student_doc = student_collection.find_one({"_id": ObjectId(student_id)})
    if not student_doc:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check if student already in class
    if student_id in class_doc["student"]:
        raise HTTPException(status_code=400, detail="Student already in class")

    # Retrieve student details
    student_details = {
        "_id": ObjectId(student_id),
        "name": student_doc["name"],
        "email": student_doc["email"]
    }
    # Update the class document to add the student ID
    result = class_collection.update_one(
        {"_id": ObjectId(class_id)},
        {"$addToSet": {"student": student_details}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Student already in class")

    return {"message": "Student added to class successfully"}



# Remove a student from the class
@classe.delete("/classes/{class_id}/students/{student_id}", dependencies=[Depends(jwtBearer())], tags=["class"])
async def remove_student_from_class(
    class_id: str = Path(..., title="The ID of the class"),
    student_id: str = Path(..., title="The ID of the student")
):
    # Check if class exists
    class_doc = class_collection.find_one({"_id": ObjectId(class_id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    # Check if student exists
    student_doc = student_collection.find_one({"_id": ObjectId(student_id)})
    if not student_doc:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check if student is in the class
    if student_id not in [str(student['_id']) for student in class_doc["student"]]:
        raise HTTPException(status_code=400, detail="Student is not in this class")

    # Update the class document to remove the student ID
    result = class_collection.update_one(
        {"_id": ObjectId(class_id)},
        {"$pull": {"student": {"_id": ObjectId(student_id)}}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to remove student from class")

    return {"message": "Student removed from class successfully"}

