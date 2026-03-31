from fastapi import Depends, HTTPException, status, Header
from jose import jwt
import requests

TENANT_ID = "4ac50105-0c66-404e-a107-7cbd8a9a6442"
CLIENT_ID = "7c7d51e4-7760-47b9-8fdd-20227453f79e"
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

try:
    response = requests.get(JWKS_URL)
    response.raise_for_status()
    jwks = response.json()
except Exception as e:
    print("FAILED TO FETCH AZURE JWKS:", e)
    jwks = {"keys": []}

def verify_azure_token(authorization: str = Header(None)):
    if authorization is None or not authorization.startswith("Bearer "):
        print("DEBUG AUTH FIX: Missing or invalid Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split("Bearer ")[1]
    
    try:
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break

        if rsa_key:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=CLIENT_ID,
                issuer=f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
            )
            return payload
        else:
            print("DEBUG AUTH FIX: Unable to find appropriate key")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to find appropriate key")
            
    except jwt.ExpiredSignatureError:
        print("DEBUG AUTH FIX: Token has expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.JWTClaimsError as e:
        print(f"DEBUG AUTH FIX: Incorrect claims, please check audience and issuer. Error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect claims, please check audience and issuer")
    except Exception as e:
        print(f"DEBUG AUTH FIX: Unable to parse authentication token: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Unable to parse authentication token: {str(e)}")

def verify_manager_role(token_payload: dict = Depends(verify_azure_token)):
    roles = token_payload.get("roles", [])
    if not isinstance(roles, list):
        roles = []
    
    # Check if user has required roles for L&D Portal (AdminViewer, LDManager, Admin)
    allowed_roles = ["adminviewer", "ldmanager", "admin"]
    user_roles = [r.lower() for r in roles]
    
    if not any(role in allowed_roles for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not possess the required Active Directory roles to access the L&D portal"
        )
        
    # Standardize the identifying username since Azure passes different fields based on the token flavor
    token_payload["identified_username"] = token_payload.get("preferred_username") or token_payload.get("upn") or token_payload.get("oid")
    
    return token_payload
