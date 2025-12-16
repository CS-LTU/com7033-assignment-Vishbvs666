from __future__ import annotations

from app import create_app
from app.db.mongo import get_patient_collection


def dedupe() -> None:
    coll = get_patient_collection()

    # Find duplicate original_id (ignore None/manual patients)
    pipeline = [
        {"$match": {"original_id": {"$type": "int"}}},
        {"$group": {"_id": "$original_id", "ids": {"$push": "$_id"}, "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}},
    ]

    dups = list(coll.aggregate(pipeline))
    print(f"Found {len(dups)} duplicate original_id groups.")

    deleted_total = 0

    for g in dups:
        original_id = g["_id"]
        ids = g["ids"]

        # Keep the first, delete the rest (simple + safe)
        keep_id = ids[0]
        delete_ids = ids[1:]

        res = coll.delete_many({"_id": {"$in": delete_ids}})
        deleted_total += res.deleted_count

        print(f"original_id={original_id}: kept={keep_id}, deleted={res.deleted_count}")

    print(f"\nDONE. Total deleted duplicates: {deleted_total}")


def main() -> None:
    app = create_app()
    with app.app_context():
        dedupe()


if __name__ == "__main__":
    main()
