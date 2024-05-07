from fastapi import APIRouter, Body, HTTPException, Path, Depends
from config.database import db
from models.staffs import StaffLogin
from auth.jwt_handler import signJWT
from pydantic import EmailStr
import bcrypt

staff = APIRouter()

staff_collection = db ["staff_collection"]

# Get all staff from the database
@staff.get("/staff", tags=["Admin"])
async def get_staff():
    staff_list = []
    for staff in staff_collection.find():
        staff_id = str(staff["_id"])
        name = staff["name"]
        email = staff["email"]
        password = staff["password"]
        
        staff_list.append({
            "staff_id": staff_id,
            "name": name,
            "email": email,
            "password": password
        })
    return staff_list


# Create a new staff member
@staff.post("/staff/insert", tags=["Admin"])
async def staff_signup(name: str, email: EmailStr, password: str):
    # Check if email already exists in the database
    existing_staff = staff_collection.find_one({"email": email})
    if existing_staff:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
     
    staff_data = {
        "name": name,
        "email": email,
        "password": hashed_password
    }

    # Insert staff member into MongoDB collection
    staff_collection.insert_one(staff_data)
    
    return signJWT(email)


# User Login
@staff.post("/staff/login", tags=["Teacher_authentication"])
async def staff_login(email: EmailStr, password: str):
    try:
        # Search for staff in MongoDB collection
        staff = staff_collection.find_one({"email": email})
        if not staff:
            raise HTTPException(status_code=401, detail="Incorrect email")
        
        # Retrieve the hashed password from the database
        stored_hashed_password = staff["password"]
        
        # Verify the password
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Incorrect password")

        # Generate JWT token
        jwt_token = signJWT(email)
        
        # Return success message along with JWT token
        return {"message": "Login successful", "token": jwt_token}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to authenticate user")


@staff.post("/staff/loginn", tags=["Teacher_authentication"])
async def staff_login(staff_login: StaffLogin = Body(default=None)):
    # Search for user in MongoDB collection
    staff = staff_collection.find_one({"email": staff_login.email})
    if not staff:
        raise HTTPException(status_code=401, detail="Incorrect email")

    # Verify the password
    if staff and bcrypt.checkpw(staff_login.password.encode('utf-8'), staff['password'].encode('utf-8')):
        # Generate JWT token
        jwt_token = signJWT(staff_login.email)
        
        # Return success message along with JWT token
        return {"message": "Login successful", "token": jwt_token}
    else:
        raise HTTPException(status_code=500, detail="Incorrect Password::Failed to authenticate")