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
feedback_columns_collection = db.feedback_columns
manager_sheets_collection = db.manager_sheets
attempts_collection = db.attempts
settings_collection = db.settings
