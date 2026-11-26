#!/usr/bin/env python3
"""Create/update a Google Wallet profile pass and print its save link."""
import argparse
import base64
import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


WALLET_API = "https://walletobjects.googleapis.com/walletobjects/v1"
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
OAUTH_SCOPE = "https://www.googleapis.com/auth/wallet_object.issuer"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def localized(value: str, language: str) -> dict:
    return {"defaultValue": {"language": language, "value": value}}


def sign_jwt(claims: dict, private_key) -> str:
    header = {"alg": "RS256", "typ": "JWT"}
    signing_input = (
        f"{b64url(json.dumps(header, separators=(',', ':')).encode())}."
        f"{b64url(json.dumps(claims, separators=(',', ':'), ensure_ascii=False).encode())}"
    )
    signature = private_key.sign(
        signing_input.encode("ascii"), padding.PKCS1v15(), hashes.SHA256()
    )
    return f"{signing_input}.{b64url(signature)}"


def request_json(method: str, url: str, access_token: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            content = response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Google Wallet API returned HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach Google Wallet API: {error.reason}") from error
    return json.loads(content) if content else {}


def get_access_token(service_account: dict, private_key) -> str:
    now = int(time.time())
    assertion = sign_jwt(
        {
            "iss": service_account["client_email"],
            "scope": OAUTH_SCOPE,
            "aud": OAUTH_TOKEN_URL,
            "iat": now,
            "exp": now + 3600,
        },
        private_key,
    )
    request = Request(
        OAUTH_TOKEN_URL,
        data=urlencode(
            {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            }
        ).encode("ascii"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read())
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Google OAuth returned HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach Google OAuth: {error.reason}") from error
    return result["access_token"]


def image(uri: str, description: str, language: str) -> dict:
    return {
        "sourceUri": {"uri": uri},
        "contentDescription": localized(description, language),
    }


def upsert_pass(access_token: str, pass_class: dict, pass_object: dict) -> None:
    class_url = f"{WALLET_API}/genericClass"
    try:
        request_json("POST", class_url, access_token, pass_class)
        print("Created Google Wallet pass class.", file=sys.stderr)
    except RuntimeError as error:
        if "HTTP 409" not in str(error):
            raise
        print("Pass class already exists; reusing it.", file=sys.stderr)

    object_url = f"{WALLET_API}/genericObject"
    try:
        request_json("POST", object_url, access_token, pass_object)
        print("Created Google Wallet pass object.", file=sys.stderr)
    except RuntimeError as error:
        if "HTTP 409" not in str(error):
            raise
        request_json("PUT", f"{object_url}/{pass_object['id']}", access_token, pass_object)
        print("Updated the existing Google Wallet pass object.", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issuer-id", required=True, help="Google Wallet Issuer ID")
    parser.add_argument(
        "--key-file", required=True, type=Path,
        help="Path to the service-account JSON key; keep it outside the repo",
    )
    args = parser.parse_args()

    if not args.key_file.is_file():
        parser.error(f"service-account key not found: {args.key_file}")

    root = Path(__file__).resolve().parent
    design = json.loads((root / "pass-design.json").read_text())
    issuer_id = args.issuer_id.strip()
    if not issuer_id.isdigit():
        parser.error("issuer ID should be the numeric ID shown in Google Wallet Console")

    class_id = f"{issuer_id}.andreiProfile"
    object_id = f"{issuer_id}.andreiProfileCard"
    lang = design["language"]
    pass_class = {"id": class_id}
    pass_object = {
        "id": object_id,
        "classId": class_id,
        "state": "ACTIVE",
        "cardTitle": localized(design["cardTitle"], lang),
        "header": localized(design["header"], lang),
        "subheader": localized(design["subheader"], lang),
        "hexBackgroundColor": design["backgroundColor"],
        "logo": image(design["logoUrl"], "A monogram", lang),
        "heroImage": image(design["heroImageUrl"], "Andrei Parnia profile portrait", lang),
        "barcode": {
            "type": "QR_CODE",
            "value": design["portfolioUrl"],
            "alternateText": "Portfolio",
        },
        "textModulesData": [
            {"id": "row2left", "header": "Email", "body": design["email"]},
            {"id": "row2right", "header": "Phone", "body": design["phone"]},
            {"id": "row3left", "header": "Based in", "body": design["location"]},
        ],
        "linksModuleData": {
            "uris": [
                {"id": "portfolio", "uri": design["portfolioUrl"], "description": "Portfolio"},
                {"id": "linkedin", "uri": design["linkedinUrl"], "description": "LinkedIn"},
                {"id": "email", "uri": f"mailto:{design['email']}", "description": "Email"},
                {"id": "phone", "uri": design["phoneUri"], "description": "Phone"},
            ]
        },
    }

    service_account = json.loads(args.key_file.read_text())
    private_key = serialization.load_pem_private_key(
        service_account["private_key"].encode("utf-8"), password=None
    )
    access_token = get_access_token(service_account, private_key)
    upsert_pass(access_token, pass_class, pass_object)

    claims = {
        "iss": service_account["client_email"],
        "aud": "google",
        "typ": "savetowallet",
        "iat": int(time.time()),
        "origins": ["bookcp.github.io"],
        "payload": {
            "genericObjects": [{"id": object_id, "classId": class_id}],
        },
    }
    token = sign_jwt(claims, private_key)
    print(f"https://pay.google.com/gp/v/save/{token}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)
