from app.core.database import batches_collection, subjects_collection, settings_collection
import pprint

print("--- LATEST 3 BATCHES ---")
for b in list(batches_collection.find().sort('_id', -1).limit(3)):
    print(b)
    print("  -> SUBJECTS:", list(subjects_collection.find({'batch_id': b['batch_id']})))
    print("  -> SETTINGS:", list(settings_collection.find({'batch_id': b['batch_id']})))
    print("-" * 40)
