from fastapi import APIRouter, Body, HTTPException, Path, UploadFile, File, Response, Depends
from config.database import db, fs
from auth.auth_bearer import jwtBearer
from bson import ObjectId
from datetime import datetime
from gridfs import GridFS
import mimetypes
from typing import List, Dict, Any


exercise = APIRouter()
fs = GridFS(db)

class_collection = db["class_collection"]
exercise_collection = db["exercise_collection"] 

"""@exercise.get("/exercis/", dependencies=[Depends(jwtBearer())], tags=["exercise"])
async def get_exercises():
    exercises = []
    for exercise in db.exercise_collection.find():
        topic = exercise["topic"]
        class_id = exercise["class_id"]
        exercise_file_id = exercise["exercise_file_id"]
        upload_date = exercise["upload_date"]
        submission_date = exercise["submission_date"]
        
        exercises.append({
            "exercise_id": str(exercise[ "_id" ]),
            "class_id": class_id,
            "topic": topic,
            "exercise_file_id": exercise_file_id,
            "upload_date": upload_date,
            "submission_date": submission_date
        })
    return exercises"""


@exercise.get("/exercises/{class_id}", dependencies=[Depends(jwtBearer())], tags=["exercise"])
async def get_exercises_by_class(class_id: str) -> List[Dict[str, Any]]:
    # Retrieve exercises for the specified class ID
    exercises = exercise_collection.find({"class_id": class_id})

    # Prepare list of exercises for the response
    exercises_list = []
    for exercise in exercises:

        exercise_info = {
            "exercise_id": str(exercise["_id"]),
            "topic": exercise["topic"],
            "exercise_file_id": exercise["exercise_file_id"],
            "upload_date": exercise["upload_date"],
            "submission_date": exercise["submission_date"]
        }
        exercises_list.append(exercise_info)

    return exercises_list



@exercise.get("/exercises/", dependencies=[Depends(jwtBearer())], tags=["exercise"])
async def get_exercises_by_class() -> List[Dict[str, Any]]:
    exercises_by_class = {}

    # Retrieve all exercises
    exercises = exercise_collection.find()

    # Group exercises by class ID
    for exercise in exercises:
        class_id = exercise["class_id"]
        exercise_info = {
            "exercise_id": str(exercise[ "_id" ]),
            "topic": exercise["topic"],
            "exercise_file_id": exercise["exercise_file_id"],
            "upload_date": exercise["upload_date"],
            "submission_date": exercise["submission_date"]
        }
        if class_id not in exercises_by_class:
            exercises_by_class[class_id] = [exercise_info]
        else:
            exercises_by_class[class_id].append(exercise_info)

    # Convert dictionary to list of dictionaries for response
    response = [{"class_id": class_id, "exercises": exercises} for class_id, exercises in exercises_by_class.items()]

    return response



@exercise.post("/exercises/upload/", dependencies=[Depends(jwtBearer())], tags=["exercise"])
async def upload_exercise(topic: str, class_id: str, submission_date: datetime, exercise_file: UploadFile = File(...)):
    # Check if class exists
    class_doc = db.class_collection.find_one({"_id": ObjectId(class_id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    # Save file to GridFS
    exercise_file_id = fs.put(exercise_file.file, filename=exercise_file.filename)

    # Save metadata to MongoDB
    exercise = {
        "topic": topic,
        "class_id": class_id,
        "exercise_file_id": str(exercise_file_id),
        "upload_date": datetime.utcnow().isoformat(),
        "submission_date": submission_date.isoformat()
    }
    # Insert metadata into exercise collection
    inserted_id = exercise_collection.insert_one(exercise).inserted_id

    return {"message": "Exercise uploaded successfully"}



@exercise.put("/exercises/{exercise_id}", dependencies=[Depends(jwtBearer())], tags=["exercise"])
async def edit_exercise(exercise_id: str = Path(..., title="The ID of the exercise"),
                        topic: str = Body(..., title="New exercise topic"),
                        submission_date: datetime = Body(..., title="New submission date"),
                        exercise_file: UploadFile = File(None)):
    try:
        # Retrieve the exercise from the exercise collection
        exercise_data = exercise_collection.find_one({"_id": ObjectId(exercise_id)})
        if exercise_data is None:
            raise HTTPException(status_code=404, detail="Exercise not found")

        # Update the exercise topic and submission date
        update_data = {"$set": {"topic": topic, "submission_date": submission_date}}
        
        # If a new exercise file is provided, update the exercise file as well
        if exercise_file:
            # Delete the existing exercise file from GridFS
            fs.delete(ObjectId(exercise_data["exercise_file_id"]))

            # Save the new exercise file to GridFS
            new_exercise_file_id = fs.put(exercise_file.file, filename=exercise_file.filename)
            update_data["$set"]["exercise_file_id"] = str(new_exercise_file_id)

        # Update the exercise document in the exercise collection
        exercise_collection.update_one({"_id": ObjectId(exercise_id)}, update_data)

        return {"message": "Exercise updated successfully"}
    except HTTPException:
        # Re-raise HTTPException to return specific error responses
        raise
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail="Failed to update exercise")




@exercise.delete("/exercises/{exercise_id}", dependencies=[Depends(jwtBearer())], tags=["exercise"])
async def delete_exercise(exercise_id: str):
    try:
        # Check if exercise exists
        exercise = exercise_collection.find_one({"_id": ObjectId(exercise_id)})
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")

        # Delete the exercise file from GridFS
        fs.delete(ObjectId(exercise["exercise_file_id"]))

        # Delete the exercise document from the collection
        exercise_collection.delete_one({"_id": ObjectId(exercise_id)})

        return {"message": "Exercise deleted successfully"}
    except HTTPException as e:
        # Re-raise HTTPException to return specific error responses
        raise
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail="Failed to delete exercise")




@exercise.get("/exercise/download/{class_id}/{exercise_id}", dependencies=[Depends(jwtBearer())], tags=["exercise"])
async def download_exercise(class_id: str = Path(..., title="The ID of the class"), 
                            exercise_id: str = Path(..., title="The ID of the exercise")):
    try:
        # Check if the class exists
        class_data = class_collection.find_one({"_id": ObjectId(class_id)})
        if class_data is None:
            raise HTTPException(status_code=404, detail="Class not found")

        # Check if the exercise belongs to the class
        exercise_data = exercise_collection.find_one({"_id": ObjectId(exercise_id), "class_id": class_id})
        if exercise_data is None:
            raise HTTPException(status_code=404, detail="Exercise not found in this class")

        # Retrieve the exercise file from GridFS
        exercise_file_info = fs.get(ObjectId(exercise_data["exercise_file_id"]))
        if exercise_file_info is None:
            raise HTTPException(status_code=404, detail="Exercise file not found")

        # Determine media type based on file extension
        filename = exercise_file_info.filename
        media_type, _ = mimetypes.guess_type(filename)
        if media_type is None:
            media_type = "application/octet-stream"

        # Read file content into memory
        exercise_file_content = exercise_file_info.read()

        # Return file content as response
        return Response(content=exercise_file_content, media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})
    except HTTPException as e:
        # Re-raise HTTPException to return specific error responses
        raise
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail="Failed to download exercise")

