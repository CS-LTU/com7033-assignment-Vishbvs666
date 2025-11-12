from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConfigurationError

_client = None
_db = None

def init_mongo(app):
    global _client, _db
    uri = app.config.get("MONGO_URI")
    if not uri:
        return

    _client = MongoClient(uri)  # TLS handled by SRV; no need to force tls=True

    # get_default_database() requires a db name in the URI; handle both cases
    try:
        _db = _client.get_default_database()
    except ConfigurationError:
        # If URI had no default DB, fall back to a named one
        _db = _client.get_database("strokecare")

    if _db is None:
        return

    # TTL + helpful indexes
    _db.predictions.create_index([("ts", ASCENDING)], expireAfterSeconds=60 * 60 * 24 * 30)
    _db.predictions.create_index([("patient_id", ASCENDING), ("ts", ASCENDING)])
    _db.events.create_index([("ts", ASCENDING)])

def mongo_db():
    return _db
