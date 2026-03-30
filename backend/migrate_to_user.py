import pymongo
import sys

# Update this to your current email as shown in the "Active Manager" section (bottom left)
NEW_MANAGER_EMAIL = "your_actual_email@sigmoid.com" 

MONGO_URI = "mongodb+srv://admin:admin@cluster0.yljdxwr.mongodb.net/?appName=Cluster0"
DATABASE_NAME = "ld_platform"

def migrate_test_data():
    if not NEW_MANAGER_EMAIL or NEW_MANAGER_EMAIL == "your_actual_email@sigmoid.com":
        print("ERROR: Please update NEW_MANAGER_EMAIL in this script first.")
        return

    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    # 1. Update Batches
    res_batches = db.batches.update_many({'manager_id': 'dev@example.com'}, {'$set': {'manager_id': NEW_MANAGER_EMAIL}})
    print(f"Migrated {res_batches.modified_count} batches.")
    
    # 2. Update Interns
    res_interns = db.interns.update_many({'manager_id': 'dev@example.com'}, {'$set': {'manager_id': NEW_MANAGER_EMAIL}})
    print(f"Migrated {res_interns.modified_count} interns.")
    
    # 3. Update Scores
    res_scores = db.scores.update_many({'manager_id': 'dev@example.com'}, {'$set': {'manager_id': NEW_MANAGER_EMAIL}})
    print(f"Migrated {res_scores.modified_count} scores.")
    
    # 4. Update Feedback
    res_feedback = db.feedback.update_many({'manager_id': 'dev@example.com'}, {'$set': {'manager_id': NEW_MANAGER_EMAIL}})
    print(f"Migrated {res_feedback.modified_count} feedback records.")
    
    # 5. Update Settings
    res_settings = db.settings.update_many({'manager_id': 'dev@example.com'}, {'$set': {'manager_id': NEW_MANAGER_EMAIL}})
    print(f"Migrated {res_settings.modified_count} settings records.")
    
    # 6. Update Chat History
    res_chat = db.chat_history.update_many({'manager_id': 'dev@example.com'}, {'$set': {'manager_id': NEW_MANAGER_EMAIL}})
    print(f"Migrated {res_chat.modified_count} chat sessions.")

    print("\nSUCCESS: All dev@example.com data has been transferred to your account.")

if __name__ == "__main__":
    migrate_test_data()
