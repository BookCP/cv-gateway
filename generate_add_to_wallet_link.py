#!/usr/bin/env python3
"""Create a Google Wallet save link locally from a service-account key."""
import argparse
import base64
import json
import sys
import time
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def localized(value: str, language: str) -> dict:
    return {"defaultValue": {"language": language, "value": value}}


def image(uri: str, description: str, language: str) -> dict:
    return {
        "sourceUri": {"uri": uri},
        "contentDescription": localized(description, language),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issuer-id", required=True, help="Google Wallet Issuer ID")
    parser.add_argument("--key-file", required=True, type=Path,
                        help="Path to the service-account JSON key; keep it outside the repo")
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
    claims = {
        "iss": "",
        "aud": "google",
        "typ": "savetowallet",
        "iat": int(time.time()),
        "origins": [],
        "payload": {
            "genericClasses": [{"id": class_id}],
            "genericObjects": [pass_object],
        },
    }
    service_account = json.loads(args.key_file.read_text())
    claims["iss"] = service_account["client_email"]
    header = {"alg": "RS256", "typ": "JWT"}
    signing_input = f"{b64url(json.dumps(header, separators=(',', ':')).encode())}.{b64url(json.dumps(claims, separators=(',', ':'), ensure_ascii=False).encode())}"
    private_key = serialization.load_pem_private_key(
        service_account["private_key"].encode("utf-8"), password=None
    )
    signature = private_key.sign(signing_input.encode("ascii"), padding.PKCS1v15(), hashes.SHA256())
    token = f"{signing_input}.{b64url(signature)}"
    save_url = f"https://pay.google.com/gp/v/save/{token}"
    if len(token) > 1800:
        print(f"Note: signed token is {len(token)} characters; Google recommends keeping it below 1800 for link compatibility.", file=sys.stderr)
    print(save_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
