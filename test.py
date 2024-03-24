import pymongo

myclient = pymongo.MongoClient("mongodb+srv://niraj:pujari@db.ssbifha.mongodb.net/")
db = myclient["db"]
signup_collection = db["signup"]

for x in signup_collection.find({},{ "_id": 0}):
  print(x)
