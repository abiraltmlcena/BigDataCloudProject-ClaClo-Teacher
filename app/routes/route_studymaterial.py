from fastapi import APIRouter, Body, HTTPException, Path, UploadFile, File, Response, Depends
from ..config.database import db, fs
from ..auth.auth_bearer import jwtBearer
from bson import ObjectId
from datetime import datetime
from gridfs import GridFS
import mimetypes
from typing import List, Dict, Any

studymaterial = APIRouter()
fs = GridFS(db)

class_collection = db["class_collection"]
studymaterial_collection = db["studymaterial_collection"] 

"""@studymaterial.get("/study_materials/", dependencies=[Depends(jwtBearer())], tags=["studymaterial"])
async def get_study_materials():
    study_materials = []
    for study_material in db.studymaterial_collection.find():
        class_id = str(study_material["class_id"])
        topic = study_material["topic"]
        file_id = study_material["file_id"]
        upload_date = study_material["upload_date"]
        
        study_materials.append({
            "class_id": class_id,
            "study_material_id": str(study_material["_id"]),
            "topic": topic,
            "file_id": file_id,
            "upload_date": upload_date
        })
    return study_materials"""


@studymaterial.get("/materials/", dependencies=[Depends(jwtBearer())], tags=["studymaterial"])
async def get_study_materials_by_class() -> List[Dict[str, Any]]:
    study_materials_by_class = {}

    # Retrieve all study materials
    study_materials = db.studymaterial_collection.find()

    # Group study materials by class ID
    for material in study_materials:
        class_id = material["class_id"]
        material_info = {
            "study_material_id": str(material["_id"]),
            "topic": material["topic"],
            "file_id": material["file_id"],
            "upload_date": material["upload_date"]
        }
        if class_id not in study_materials_by_class:
            study_materials_by_class[class_id] = [material_info]
        else:
            study_materials_by_class[class_id].append(material_info)

    # Convert dictionary to list of dictionaries for response
    response = [{"class_id": class_id, "study_materials": materials} for class_id, materials in study_materials_by_class.items()]

    return response


@studymaterial.post("/upload/", dependencies=[Depends(jwtBearer())], tags=["studymaterial"])
async def upload_study_material(class_id: str, topic: str, material: UploadFile = File(...)):
    # Check if class exists
    class_doc = class_collection.find_one({"_id": ObjectId(class_id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Save file to GridFS
    file_id = fs.put(material.file, filename=material.filename)
    
    # Save metadata to MongoDB
    study_material = {
        "class_id": class_id,
        "topic": topic,
        "file_id": str(file_id),
        "upload_date": datetime.utcnow()
    }
    # Insert metadata into study_materials collection
    db.studymaterial_collection.insert_one(study_material)
    
    return {"message": "Study material uploaded successfully"}




@studymaterial.get("/study_materials/{class_id}", dependencies=[Depends(jwtBearer())], tags=["studymaterial"])
async def get_study_materials_by_class(class_id: str):
    try:
        # Check if class exists
        class_doc = class_collection.find_one({"_id": ObjectId(class_id)})
        if not class_doc:
            raise HTTPException(status_code=404, detail="Class not found")

        # Retrieve study materials for the given class ID
        study_materials = []
        for file_info in db.studymaterial_collection.find({"class_id": class_id}):
            topic = file_info["topic"]
            file_id = file_info["file_id"]
            upload_date = file_info["upload_date"]

            study_materials.append({
                "topic": topic,
                "upload_date": upload_date,
                "file_id": file_id
            })

        return study_materials
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail="Failed to retrieve study materials")




@studymaterial.put("/update/{study_material_id}", dependencies=[Depends(jwtBearer())], tags=["studymaterial"])
async def update_study_material(study_material_id: str = Path(..., title="The ID of the study material"), new_file: UploadFile = File(...), new_topic: str = Body(..., title="New study topic")):
    try:
        # Retrieve study material from the study material collection
        study_material = db.studymaterial_collection.find_one({"_id": ObjectId(study_material_id)})
        if study_material is None:
            raise HTTPException(status_code=404, detail="Study material not found")

        # Delete the existing file from GridFS
        fs.delete(ObjectId(study_material["file_id"]))

        # Save the new file to GridFS
        new_file_id = fs.put(new_file.file, filename=new_file.filename)

        # Update the study material document with the new file ID and topic
        db.studymaterial_collection.update_one({"_id": ObjectId(study_material_id)}, {"$set": {"file_id": str(new_file_id), "topic": new_topic}})

        return {"message": "Study material file and topic updated successfully"}
    except HTTPException:
        # Re-raise HTTPException to return specific error responses
        raise
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail="Failed to update study material file and topic")



@studymaterial.get("/download/{class_id}/{study_material_id}", dependencies=[Depends(jwtBearer())], tags=["studymaterial"])
async def download_study_material(class_id: str = Path(..., title="The ID of the class"),
                                  study_material_id: str = Path(..., title="The ID of the study material")):
    try:
        # Verify if class exists
        class_doc = db.class_collection.find_one({"_id": ObjectId(class_id)})
        if class_doc is None:
            raise HTTPException(status_code=404, detail="Class not found")

        # Verify if study material exists and belongs to the specified class
        study_material = db.studymaterial_collection.find_one({"_id": ObjectId(study_material_id), "class_id": class_id})
        if study_material is None:
            raise HTTPException(status_code=404, detail="Study material not found for this class")

        # Retrieve file from GridFS using the file ID stored in the study material
        file_info = fs.get(ObjectId(study_material["file_id"]))
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
        raise HTTPException(status_code=500, detail="Failed to download study material")


@studymaterial.delete("/delete/{class_id}/{study_material_id}", dependencies=[Depends(jwtBearer())], tags=["studymaterial"])
async def delete_study_material(class_id: str = Path(..., title="The ID of the class"),
                                study_material_id: str = Path(..., title="The ID of the study material")):
    try:
        # Check if class exists
        class_doc = class_collection.find_one({"_id": ObjectId(class_id)})
        if not class_doc:
            raise HTTPException(status_code=404, detail="Class not found")

        # Retrieve study material from the study material collection
        study_material = db.studymaterial_collection.find_one({"_id": ObjectId(study_material_id), "class_id": class_id})
        if study_material is None:
            raise HTTPException(status_code=404, detail="Study material not found for this class")

        # Delete the file from GridFS
        fs.delete(ObjectId(study_material["file_id"]))

        # Delete the study material document from the collection
        db.studymaterial_collection.delete_one({"_id": ObjectId(study_material_id), "class_id": class_id})

        return {"message": "Study material deleted successfully"}
    except HTTPException:
        # Re-raise HTTPException to return specific error responses
        raise
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail="Failed to delete study material")
