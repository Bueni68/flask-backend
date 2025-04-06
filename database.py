import os
from pymongo import MongoClient
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()
DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD"))

MONGO_URI = f"mongodb+srv://mbemail:{DB_PASSWORD}@clusterrfid.rqitdfg.mongodb.net/?retryWrites=true&w=majority&appName=ClusterRFID"
client = MongoClient(MONGO_URI)
db = client["flaskDB"]

users_collection = db["users"]
temp_users_collection = db["temp_users"]
history_collection = db["history"]
stations_collection = db["stations"]
estimated_times_collection = db["estimated_times"]