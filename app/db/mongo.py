'''
===========================================================
StrokeCare Web Application — Secure Software Development
Author: Vishvapriya Sangvikar

Course: COM7033 – MSc Data Science & Artificial Intelligence
Student ID: 2415083
Institution: Leeds Trinity University
Assessment: Assessment 1 – Software Artefact (70%)
AI Statement: Portions of this file were drafted or refined using
    generative AI for planning and editing only,
    as permitted in the module brief.
===========================================================
'''

# app/db/mongo.py
from __future__ import annotations

from typing import Any

from flask import current_app, g
from pymongo import MongoClient


def _get_mongo_client() -> MongoClient:
    """
    Lazily create a MongoClient bound to the current Flask app context.
    Re-used for the duration of the request / CLI command via flask.g.
    """
    if "mongo_client" not in g:
        uri = current_app.config["MONGO_URI"]  # KeyError fixed by Config.MONGO_URI
        g.mongo_client = MongoClient(uri)
    return g.mongo_client


def get_patient_collection():
    """
    Return the MongoDB collection used for patient records.
    Names are configurable via Config.
    """
    client = _get_mongo_client()
    db_name = current_app.config.get("MONGO_DB_NAME", "strokecare")
    coll_name = current_app.config.get("MONGO_PATIENTS_COLLECTION", "patients")
    return client[db_name][coll_name]


def close_mongo_client(exception: Exception | None = None) -> None:  # pragma: no cover
    """
    Teardown handler – closes the client at the end of the request / CLI execution.
    """
    client: MongoClient | None = g.pop("mongo_client", None)
    if client is not None:
        client.close()
