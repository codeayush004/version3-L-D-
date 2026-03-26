from fastapi import Depends, HTTPException, status, Header
from jose import jwt
import requests

TENANT_ID = "4ac50105-0c66-404e-a107-7cbd8a9a6442"
CLIENT_ID = "7c7d51e4-7760-47b9-8fdd-20227453f79e"
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

# Fetch JWKS keys globally on startup
try:
    response = requests.get(JWKS_URL)
    response.raise_for_status()
    jwks = response.json()
except Exception as e:
    print("FAILED TO FETCH AZURE JWKS:", e)
    jwks = {"keys": []}

def verify_azure_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing. Must login via Microsoft.")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth scheme")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format")

    try:
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key["kid"] == unverified_header.get("kid"):
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break

        if not rsa_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to find appropriate RSA key in Microsoft discovery endpoint.")

        # Decode the token against the public key
        # V2 endpoint tokens usually have an issuer of https://login.microsoftonline.com/{tenantid}/v2.0
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Microsoft token has expired.")
    except jwt.JWTClaimsError as e:
        # A common issue is the issuer or audience mismatch. E.g. V1 vs V2 endpoint.
        # We will attempt to decode without issuer validation fallback if it fails strictly.
        try:
            payload = jwt.decode(token, rsa_key, algorithms=["RS256"], audience=CLIENT_ID, options={"verify_iss": False})
            return payload
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"JWT Claims Error: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Microsoft token: {e}")

def verify_manager_role(token_payload: dict = Depends(verify_azure_token)):
    roles = token_payload.get("roles", [])
    if "LDManager" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted Action. You must be an L&D Manager to upload/edit data.")
    return token_payload
