def verify_azure_token():
    return {
        "preferred_username": "dev@example.com",
        "roles": ["LDManager", "Admin"],
        "name": "Dev User"
    }

def verify_manager_role():
    return {
        "identified_username": "dev@example.com"
    }
