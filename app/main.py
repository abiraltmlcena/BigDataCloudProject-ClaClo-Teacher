from fastapi import FastAPI, Body, Depends
from .routes.route_staff import staff
from .routes.route_student import student
from .routes.route_class import classe
from .routes.route_studymaterial import studymaterial
from .routes.route_exercise import exercise
from .routes.route_answer import answer

app = FastAPI()

app.include_router(staff)
app.include_router(student)
app.include_router(classe)
app.include_router(studymaterial)
app.include_router(exercise)
app.include_router(answer)






