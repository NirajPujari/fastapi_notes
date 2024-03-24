from pymongo import MongoClient
from pymongo.server_api import ServerApi

api_key = "ygyrlTfv7tqVznf"

# Checking if the api_key is correct.
def key_checker(key):
    return api_key == key

# MongoDB connection URI
MONGO_URI = "mongodb+srv://niraj:pujari@db.ssbifha.mongodb.net/"

# Connect to MongoDB server
client = MongoClient(MONGO_URI, server_api=ServerApi("1"))

try:
    # Check if the connection is successful by pinging the MongoDB server
    client.admin.command("ping")
    print("Connected to DB")
    print("Api Key:", api_key)
except Exception as e:
    # If connection fails, print the error message
    print(e)

# Database and collections
db = client["db"]
signup_collection = db["signup"]
login_collection = db["login"]
notes_collection = db["notes"]
