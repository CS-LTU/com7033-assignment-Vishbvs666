# app/db/mongo.py
from __future__ import annotations

from typing import Any, Dict, Optional

from flask import current_app, g
from pymongo import MongoClient


def _get_mongo_client() -> MongoClient:
    client: Optional[MongoClient] = g.get("mongo_client")
    if client is None:
        uri = current_app.config["MONGO_URI"]
        client = MongoClient(uri, tls="mongodb+srv://" in uri)
        g.mongo_client = client
    return client


def get_patient_collection():
    client = _get_mongo_client()
    dbname = current_app.config.get("MONGO_DBNAME", "strokecare")
    return client[dbname]["patients"]


def close_mongo_client() -> None:
    client: Optional[MongoClient] = g.pop("mongo_client", None)
    if client is not None:
        client.close()
