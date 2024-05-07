from fastapi import APIRouter, Body, HTTPException, Path, Depends, Response, UploadFile
from ..config.database import db, fs
from ..auth.auth_bearer import jwtBearer
from bson import ObjectId
from gridfs import GridFS
import mimetypes
from typing import List, Dict, Any

answer = APIRouter()

excercise_and_assignment = db["excercise_and_assignment"]


@answer.get("/answers/",dependencies=[Depends(jwtBearer())], tags=["answers"])
async def get_answers_group_by_classID_and_exerciseID() -> List[Dict[str, Any]]:
    answers_by_class_and_exercise = {}

    # Retrieve answers for the given class ID and exercise ID
    answers = db.excercise_and_assignment.find()

    # Group answers by class ID and exercise ID
    for ans in answers:
        class_id = ans["class_id"]
        exercise_id = ans["excercise_Id"]
        ans_info = {
            "answer_id": str(ans["_id"]),
            "student_id": ans["student_Id"],
            "topic_name": ans["topic_name"],
            "file_id": ans["file_id"],
            "upload_date": ans["upload_date"]
        }
        if (class_id, exercise_id) not in answers_by_class_and_exercise:
            answers_by_class_and_exercise[(class_id, exercise_id)] = [ans_info]
        else:
            answers_by_class_and_exercise[(class_id, exercise_id)].append(ans_info)

    # Convert dictionary to list of dictionaries for response
    response = [{"class_id": class_id, "exercise_id": exercise_id, "answers": answers} 
                for (class_id, exercise_id), answers in answers_by_class_and_exercise.items()]

    return response



@answer.get("/answers/student/{student_id}/exercise/{exercise_id}", dependencies=[Depends(jwtBearer())], tags=["answers"])
async def get_student_answer_by_ids(student_id: str = Path(..., title="Student ID"),
                                    exercise_id: str = Path(..., title="Exercise ID")):
    
    # Check if the exercise exists
    exercise = db.exercise_collection.find_one({"_id": ObjectId(exercise_id)})
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    # Check if the student exists
    student = db.student_collection.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Retrieve the answer for the given exercise and student
    answer = db.excercise_and_assignment.find_one({"excercise_Id": exercise_id, "student_Id": student_id})
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found for this student and exercise")

    # Construct the response
    student_answer = {
        "answer_id": str(answer["_id"]),  
        "topic_name": answer["topic_name"],
        "class_id": answer["class_id"],
        "file_id": answer["file_id"],
        "upload_date": answer["upload_date"]
    }
    
    return student_answer


@answer.get("/answer/download/{student_id}/{exercise_id}", dependencies=[Depends(jwtBearer())], tags=["answers"])
async def download_answer(student_id: str = Path(..., title="Student ID"),
                                    exercise_id: str = Path(..., title="Exercise ID")):
    try:
        # Check if the exercise exists
        exercise = db.exercise_collection.find_one({"_id": ObjectId(exercise_id)})
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        # Check if the student exists
        student = db.student_collection.find_one({"_id": ObjectId(student_id)})
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        # Retrieve the answer for the given exercise and student
        answer = db.excercise_and_assignment.find_one({"excercise_Id": exercise_id, "student_Id": student_id})
        if not answer:
            raise HTTPException(status_code=404, detail="Answer not found for this student and exercise")
        # Retrieve file from GridFS using the file ID stored in the study material
        file_info = fs.get(ObjectId(answer["file_id"]))
        if file_info is None:
            raise HTTPException(status_code=404, detail="File not found")
        # Determine media type based on file extension
        filename = file_info.filename
        media_type, _ = mimetypes.guess_type(filename)
        if media_type is None:
                media_type = "application/octet-stream"
        # Read file content into memory
        file_content = file_info.read()
        # Return file content as response
        return Response(content=file_content, media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})
    except HTTPException:
        # Re-raise HTTPException to return specific error responses
        raise
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail="Failed to download answer")



@answer.put("/answer/feedback/{answer_id}", dependencies=[Depends(jwtBearer())], tags=["answers"])
async def update_feedback(answer_id: str = Path(..., title="Answer ID"),
                          marks: float = Body(..., title="Marks"),
                          feedback: str = Body(..., title="Feedback")):
    try:
        # Convert answer ID to ObjectId
        answer_id_obj = ObjectId(answer_id)

        # Check if the answer exists
        answer = db.excercise_and_assignment.find_one({"_id": answer_id_obj})
        if not answer:
            raise HTTPException(status_code=404, detail="Answer not found")

        # Update the answer with new feedback and marks
        db.excercise_and_assignment.update_one(
            {"_id": answer_id_obj},
            {"$set": {"marks": marks, "feedback": feedback}}
        )

        return {"message": "Feedback and marks updated successfully"}
    except HTTPException:
        # Re-raise HTTPException to return specific error responses
        raise
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail="Failed to update feedback and marks")


@answer.get("/answers/mark/{answer_id}", dependencies=[Depends(jwtBearer())], tags=["answers"])
async def get_mark_by_answerid(answer_id: str = Path(..., title="Answer ID")):    
    # Check if the answer exists
    answer = db.excercise_and_assignment.find_one({"_id": ObjectId(answer_id)})
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    # Retrieve answers for the given answer id
    answers = []
    for answer in db.excercise_and_assignment.find({"_id": ObjectId(answer_id)}):
        student_id = answer["student_Id"]
        feedback = answer["feedback"]
        mark = answer["marks"]
        
        
        answers.append({
            "student_id": student_id,
            "feedback": feedback,
            "mark": mark
        })
        
    return answers