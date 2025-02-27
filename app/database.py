
import os
from dotenv import load_dotenv
from pymongo.database import Database
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URI)
db: Database = client[DB_NAME]

def get_database() -> Database:
    return db
