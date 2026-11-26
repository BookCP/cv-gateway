# Google Wallet profile pass

This folder contains the files for a native Google Wallet Generic pass. The design settings use the forest-green background, your CV portrait, the monogram logo, portfolio QR code, and contact details.

Google Wallet controls the card layout. The pass settings choose its color, images, barcode, title, and fields. The hero image and logo are served from this folder on GitHub Pages.

## Create an Add to Google Wallet link

1. Create a Google Wallet issuer account and note its numeric Issuer ID.
2. Enable the Google Wallet API in Google Cloud.
3. Create a service account and invite its email in Google Pay & Wallet Console with Developer access.
4. Create a JSON key for the service account and keep it outside this repository. Never commit or share the key.
5. From the repository root, install the dependency:

   ```sh
   python3 -m pip install -r wallet-pass/requirements.txt
   ```

6. Generate a signed save link locally:

   ```sh
   python3 wallet-pass/generate_add_to_wallet_link.py --issuer-id YOUR_ISSUER_ID --key-file /path/to/service-account.json
   ```

7. Open the generated link on a Google Wallet account authorized for the issuer. Demo Mode limits who can save the pass; publishing access is required for general distribution.

The generator reads `pass-design.json`, signs a Wallet JWT locally, and prints the link. It does not upload or store the service-account key.
