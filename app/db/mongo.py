from __future__ import annotations
from flask import g, current_app
from pymongo import MongoClient

def get_db():
    if "mongo_db" not in g:
        uri = current_app.config["MONGO_URI"]
        name = current_app.config["MONGO_DBNAME"]
        g.mongo_client = MongoClient(uri, uuidRepresentation="standard")
        g.mongo_db = g.mongo_client[name]
    return g.mongo_db

def close_mongo(e=None):
    client = getattr(g, "mongo_client", None)
    if client:
        client.close()
