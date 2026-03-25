from pymongo import MongoClient
import certifi
from .config import settings

client = MongoClient(settings.MONGO_URI, tlsCAFile=certifi.where())
db = client[settings.DATABASE_NAME]

managers_collection = db.managers
interns_collection = db.interns
scores_collection = db.scores
feedback_collection = db.feedback
subjects_collection = db.subjects
batches_collection = db.batches

settings_collection = db.settings
