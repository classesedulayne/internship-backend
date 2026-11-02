from pymongo import MongoClient
from django.conf import settings
from bson import ObjectId
import datetime

client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

# Collections
applications_col = db["internship_applications"]
users_col = db["users"]
settings_col = db["settings"]
programs_col = db["programs"]
domains_col = db["domains"]

# Helper to serialize MongoDB docs to JSON friendly dicts
def serialize_doc(doc):
    if not doc:
        return None
    doc_copy = dict(doc)
    if "_id" in doc_copy:
        doc_copy["id"] = str(doc_copy.pop("_id"))
    for key, value in doc_copy.items():
        if isinstance(value, ObjectId):
            doc_copy[key] = str(value)
        elif isinstance(value, (datetime.datetime, datetime.date)):
            doc_copy[key] = value.isoformat()
        elif isinstance(value, list):
            doc_copy[key] = [serialize_doc(i) if isinstance(i, dict) else i for i in value]
        elif isinstance(value, dict):
            doc_copy[key] = serialize_doc(value)
    return doc_copy

def serialize_docs(docs):
    return [serialize_doc(doc) for doc in docs]
