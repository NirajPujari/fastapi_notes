from fastapi import APIRouter, HTTPException, Header, Query
from db.connection import key_checker, notes_collection
from auth.endpoints import auth_user_login

router = APIRouter()

# Note Endpoints
# GET /api/search?q=:query: search for notes based on keywords for the authenticated user.

# Endpoint to search the note
@router.get("/search")
async def search_notes(
    title: str = Query(None), token: int = Header(None), key: str = Header(None)
):
    if not key_checker(key):
        raise HTTPException(status_code=401, detail="Unauthorized access.")
    user = auth_user_login(token)
    if title == "" and title == None:
        return [i for i in notes_collection.find({"user": user}, {"_id": 0, "user": 0})]
    else:
        return [i for i in notes_collection.find({"user": user, "title": title}, {"_id": 0, "user": 0})]
