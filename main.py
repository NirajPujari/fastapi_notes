from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from pydantic import BaseModel
from random import randint
from re import search, split
from pymongo.server_api import ServerApi

app = FastAPI()
client = MongoClient(
    "mongodb+srv://niraj:pujari@db.ssbifha.mongodb.net/", server_api=ServerApi("1")
)

try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["db"]
signup_collection = db["signup"]
login_collection = db["login"]
notes_collection = db["notes"]

# Authentication Endpoints
# POST /api/auth/signup: create a new user account.
# POST /api/auth/login: log in to an existing user account and receive an access token.
# Extra Delete /api/auth/login/id: log out the user with the given token.


class UserSignUp(BaseModel):
    userid: str
    useremail: str
    password: str


class UserLogin(BaseModel):
    userid: str
    password: str


# Endpoint to create a new user
@app.post("/api/auth/signup")
async def create_user(user: UserSignUp):
    user = user.dict()
    if not signup_collection.find_one({"userid": user["userid"]}):
        inserted_item = signup_collection.insert_one(user)
        return {
            "id": str(inserted_item.inserted_id),
            "message": "User created successfully",
        }
    else:
        raise HTTPException(status_code=409, detail="User already exists.")


# Endpoint to create a new token and check if the user is already signup and will authenticate the user also
@app.post("/api/auth/login")
async def get_token(user: UserLogin):
    user = user.dict()
    if signup_collection.find_one(
        {"userid": user["userid"], "password": user["password"]}
    ):
        if not login_collection.find_one({"userid": user["userid"]}):
            token = randint(100000, 1000000)
            login_collection.insert_one({"token": token, "userid": user["userid"]})
            return {"token": token, "message": "User loged in successfully"}
        else:
            raise HTTPException(status_code=409, detail="User already in database")
    else:
        raise HTTPException(status_code=404, detail="User not found")


# Endpoint to delete a user
@app.delete("/api/auth/login/{token}")
async def get_token(token: int):
    deleteduser = login_collection.delete_one({"token": token})
    if deleteduser.deleted_count == 1:
        return {"message": "User loged out successfully"}
    else:
        raise HTTPException(status_code=404, detail="Item not found")


# Note Endpoints
# GET /api/notes: get a list of all notes for the authenticated user.
# GET /api/notes/id: get a note by ID for the authenticated user.
# POST /api/notes: create a new note for the authenticated user.
# PUT /api/notes/id: update an existing note by ID for the authenticated user.
# DELETE /api/notes/id: delete a note by ID for the authenticated user.
# POST /api/notes/:id/share: share a note with another user for the authenticated user.
# GET /api/search?q=:query: search for notes based on keywords for the authenticated user.


class Note(BaseModel):
    user: str
    title: str
    content: str


class UpdatedNote(BaseModel):
    user: str
    title: str
    content: str


class ShareNote(BaseModel):
    fromuser: str
    touser: str


# Endpoint to create a new note
@app.post("/api/notes")
async def create_notes(note: Note):
    note = note.dict()
    id = randint(10000, 100000)
    note.setdefault("id", id)
    notes_collection.insert_one(note)
    return {"id": id, "message": "Note created successfully"}


# Endpoint to fetch all the notes
@app.get("/api/notes")
async def get_notes(user: dict):
    return [
        {"id": i["id"], "title": i["title"], "content": i["content"]}
        for i in notes_collection.find({"user": user["user"]})
    ]


# Endpoint to fetch single note using id
@app.get("/api/notes/{id}")
async def get_notes_by_id(id: int, user: dict):
    note = notes_collection.find_one({"id": id, "user": user["user"]})
    if note:
        return {"id": note["id"], "title": note["title"], "content": note["content"]}
    else:
        raise HTTPException(status_code=404, detail="Note not found")


# Endpoint to update the already present note
@app.put("/api/notes/{id}")
async def update_note(id: int, note: UpdatedNote):
    note = note.dict()
    updatednote = notes_collection.update_one(
        {"id": id, "user": note["user"]}, {"$set": note}
    )
    if updatednote.modified_count == 1:
        return {"message": "Note updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Item not found")


# Endpoint to delete an note from the db
@app.delete("/api/notes/{id}")
async def delete_note(id: int, user: dict):
    deletednote = notes_collection.delete_one({"id": id, "user": user["user"]})
    if deletednote.deleted_count == 1:
        return {"message": "Item deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Item not found")


# Endpoint to note between user
@app.post("/api/notes/{id}/share")
async def share_note(id: int, userdata: ShareNote):
    userdata = userdata.dict()
    note = notes_collection.find_one({"id": id, "user": userdata["fromuser"]})
    if note:
        if signup_collection.find_one({"userid": userdata["touser"]}):
            notes_collection.insert_one(
                {
                    "id": id,
                    "user": userdata["touser"],
                    "title": note["title"],
                    "content": note["content"],
                }
            )
            note.setdefault("shared", []).append(userdata["touser"])
            notes_collection.update_one(
                {"id": id, "user": note["user"]}, {"$set": note}
            )
            return {"message": "Note shared successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    else:
        raise HTTPException(status_code=404, detail="Note not found")


# Endpoint to search the note
@app.get("/api/search")
async def search_notes(query: str = Query(None)):
    if search("user=\w+|,title=(\w+|\s)", query):
        text = split(",", query)
        result = [j for i in text for j in split("=", i)]
        result.pop(0)
        result.pop(1)
        if result[1] == "_":
            return [
                {"id": i["id"], "title": i["title"], "content": i["content"]}
                for i in notes_collection.find({"user": result[0]})
            ]
        else:
            return [
                {"id": i["id"], "title": i["title"], "content": i["content"]}
                for i in notes_collection.find({"user": result[0], "title": result[1]})
            ]
    else:
        raise HTTPException(status_code=400, detail="Invalid request parameters")
