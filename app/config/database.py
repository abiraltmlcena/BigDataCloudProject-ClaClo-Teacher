from pymongo import MongoClient
from pymongo.server_api import ServerApi
from gridfs import GridFS

client = MongoClient("mongodb+srv://19274214:COMP7033@comp7033.og3ddze.mongodb.net/?retryWrites=true&w=majority&appName=COMP7033"
)

db = client.teacher_db
fs = GridFS(db)
