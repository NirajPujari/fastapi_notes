from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from db.connection import key_checker, notes_collection
from random import randint
from auth.endpoints import auth_user_login, auth_user_signup

router = APIRouter()

# Note Endpoints
# GET /api/notes: get a list of all notes for the authenticated user.
# GET /api/notes/id: get a note by ID for the authenticated user.
# POST /api/notes: create a new note for the authenticated user.
# PUT /api/notes/id: update an existing note by ID for the authenticated user.
# DELETE /api/notes/id: delete a note by ID for the authenticated user.
# POST /api/notes/:id/share: share a note with another user for the authenticated user.


class Note(BaseModel):
    title: str
    content: str


class UpdatedNote(BaseModel):
    title: str
    content: str


class ShareNote(BaseModel):
    touser: str


# Endpoint to create a new note
@router.post("")
async def create_notes(note: Note, token: int = Header(None), key: str = Header(None)):
    if not key_checker(key):
        raise HTTPException(status_code=401, detail="Unauthorized access.")

    user = auth_user_login(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    note = note.dict()
    id = randint(10000, 100000)
    note.setdefault("id", id)
    note.setdefault("user", user)
    notes_collection.insert_one(note)
    return {"id": id, "message": "Note created successfully"}


# Endpoint to fetch all the notes
@router.get("")
async def get_notes(token: int = Header(None), key: str = Header(None)):
    if not key_checker(key):
        raise HTTPException(status_code=401, detail="Unauthorized access.")
    user = auth_user_login(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return [i for i in notes_collection.find({"user": user}, {"_id": 0, "user": 0})]


# Endpoint to fetch single note using id
@router.get("/{id}")
async def get_notes_by_id(id: int, token: int = Header(None), key: str = Header(None)):
    if not key_checker(key):
        raise HTTPException(status_code=401, detail="Unauthorized access.")
    user = auth_user_login(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    note = notes_collection.find_one({"id": id, "user": user}, {"_id": 0, "user": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return note


# Endpoint to update the already present note
@router.put("/{id}")
async def update_note(
    id: int, note: UpdatedNote, token: int = Header(None), key: str = Header(None)
):
    if not key_checker(key):
        raise HTTPException(status_code=401, detail="Unauthorized access.")
    user = auth_user_login(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    note = note.dict()
    updatednote = notes_collection.update_one({"id": id, "user": user}, {"$set": note})
    if not updatednote.modified_count == 1:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"message": "Note updated successfully"}


# Endpoint to delete an note from the db
@router.delete("/{id}")
async def delete_note(id: int, token: int = Header(None), key: str = Header(None)):
    if not key_checker(key):
        raise HTTPException(status_code=401, detail="Unauthorized access.")
    user = auth_user_login(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    deletednote = notes_collection.delete_one({"id": id, "user": user})
    if not deletednote.deleted_count == 1:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"message": "Item deleted successfully"}


# Endpoint to note between user
@router.post("/{id}/share")
async def share_note(
    id: int, userdata: ShareNote, token: int = Header(None), key: str = Header(None)
):
    if not key_checker(key):
        raise HTTPException(status_code=401, detail="Unauthorized access.")
    fromuser = auth_user_login(token)
    if not fromuser:
        raise HTTPException(status_code=401, detail="Invalid token")

    userdata = userdata.dict()
    touser = auth_user_signup(userdata["touser"])
    if not touser:
        raise HTTPException(status_code=404, detail="User not found")

    if touser == fromuser:
        raise HTTPException(status_code=409, detail="Same user sharing not possible.")

    note = notes_collection.find_one({"id": id, "user": fromuser})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    notes_collection.insert_one(
        {
            "id": id,
            "user": touser,
            "title": note["title"],
            "content": note["content"],
        }
    )
    note.setdefault("shared", []).append(touser)
    notes_collection.update_one({"id": id, "user": fromuser}, {"$set": note})
    return {"message": "Note shared successfully"}
