import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv
load_dotenv(".env")

cred = credentials.Certificate("firebasecred.json")
firebase_admin.initialize_app(cred,
    {"databaseURL": "https://fflogsbot-ea63e-default-rtdb.firebaseio.com/"})


_USERS_DB = db.reference("users/")

def update_user(discord_id, fflogs_id):
    _USERS_DB.update({str(discord_id): fflogs_id})

def get_fflogs_id(discord_id):
    return _USERS_DB.child(str(discord_id)).get()

def remove_user(discord_id):
    id = get_fflogs_id(discord_id)
    if id:
        _USERS_DB.child(str(discord_id)).delete()
        return id
    else:
        return None