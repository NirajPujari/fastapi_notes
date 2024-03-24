from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from db.connection import signup_collection, login_collection, key_checker
from random import randint

router = APIRouter()

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


# Function to authenticate user login
def auth_user_login(token: int):
    # Find user in login collection based on token
    user = login_collection.find_one({"token": token}, {"_id": 0, "userid": 1})

    if user:
        return user["userid"]
    return False


# Endpoint to create a new user
def auth_user_signup(user: str, password: str = ""):
    # Check if password is provided
    if password == "":
        userwithid = signup_collection.find_one(
            {"userid": user}, {"_id": 0, "userid": 1}
        )
    else:
        userwithid = signup_collection.find_one(
            {"userid": user, "password": password}, {"_id": 0, "userid": 1}
        )

    if userwithid:
        return userwithid["userid"]
    return False


# Endpoint to create a new user
@router.post("/signup")
async def create_user(user: UserSignUp, key: str = Header(None)):
    if not key_checker(key):
        raise HTTPException(status_code=401, detail="Unauthorized access.")
    user = user.dict()
    if not auth_user_signup(user["userid"]):
        inserted_item = signup_collection.insert_one(user)
        return {
            "id": str(inserted_item.inserted_id),
            "message": "User created successfully",
        }
    else:
        raise HTTPException(status_code=409, detail="User already exists.")


# Endpoint to create a new token and check if the user is already signup and will authenticate the user also
@router.post("/login")
async def get_token(user: UserLogin, key: str = Header(None)):
    if not key_checker(key):
        raise HTTPException(status_code=401, detail="Unauthorized access.")
    user = user.dict()
    if auth_user_signup(user["userid"]):
        if auth_user_signup(user["userid"], user["password"]):
            if not login_collection.find_one({"userid": user["userid"]}):
                token = randint(10**5, 10**6)
                login_collection.insert_one({"token": token, "userid": user["userid"]})
                return {"token": token, "message": "User logged in successfully"}
            else:
                raise HTTPException(status_code=409, detail="User already loged in.")
        else:
            raise HTTPException(status_code=401, detail="Wrong Username/Password.")
    else:
        raise HTTPException(status_code=404, detail="User not found.")


# Endpoint to delete a user
@router.delete("/logout/{token}")
async def logout(token: int, key: str = Header(None)):
    if not key_checker(key):
        raise HTTPException(status_code=401, detail="Unauthorized access.")
    deleted_user = login_collection.delete_one({"token": token})
    if deleted_user.deleted_count == 1:
        return {"message": "User logged out successfully"}
    else:
        raise HTTPException(status_code=404, detail="Token not found.")
