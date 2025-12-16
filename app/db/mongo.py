from __future__ import annotations

from flask import current_app, g
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError


def _get_mongo_client() -> MongoClient:
    """
    Lazily create a MongoClient bound to the current Flask app context.
    Re-used for the duration of the request / CLI command via flask.g.
    """
    if "mongo_client" not in g:
        uri = current_app.config["MONGO_URI"]
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


def ensure_patient_indexes() -> None:
    """
    Create indexes for the patients collection.

    - Unique index on original_id (ONLY for imported Kaggle patients)
      using a partial index so manual patients (original_id=None) are allowed.
    - Helpful query indexes for your list/filter screens.
    """
    coll = get_patient_collection()

    # 1) Unique original_id for imported dataset docs (ints only)
    # NOTE: Will throw DuplicateKeyError if duplicates already exist.
    coll.create_index(
        [("original_id", ASCENDING)],
        name="uniq_original_id_if_int",
        unique=True,
        partialFilterExpression={"original_id": {"$type": "int"}},
    )

    # 2) Common query indexes (non-unique)
    coll.create_index([("system_metadata.is_active", ASCENDING)], name="idx_is_active")
    coll.create_index([("risk_assessment._level", ASCENDING)], name="idx_risk_level__underscore")
    coll.create_index([("risk_assessment.level", ASCENDING)], name="idx_risk_level")
    coll.create_index([("demographics.age", ASCENDING)], name="idx_demo_age")
    coll.create_index([("demographics.name", ASCENDING)], name="idx_demo_name")


def close_mongo_client(exception: Exception | None = None) -> None:  # pragma: no cover
    """
    Teardown handler – closes the client at the end of the request / CLI execution.
    """
    client: MongoClient | None = g.pop("mongo_client", None)
    if client is not None:
        client.close()
