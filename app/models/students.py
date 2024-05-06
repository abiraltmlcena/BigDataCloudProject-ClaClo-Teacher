from pydantic import BaseModel, Field, EmailStr

class Student(BaseModel):
    name: str
    email: EmailStr
    password: str

