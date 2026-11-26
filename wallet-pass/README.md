# Google Wallet profile pass

This folder contains the design, images, and generator for a native Google Wallet Generic pass. The design uses the forest-green background, CV portrait, monogram logo, portfolio QR code, email, phone, city, and links.

Google Wallet controls the card layout. The API sets its color, images, barcode, title, and fields.

## Create an Add to Google Wallet link

1. Create a Google Wallet issuer account and note its numeric Issuer ID.
2. Enable the Google Wallet API in Google Cloud.
3. Create a service account and invite its email in Google Pay & Wallet Console with Developer access.
4. Create a JSON key for the service account and keep it outside this repository. Never commit or share the key.
5. From the repository root, install the dependency:

   ```sh
   python3 -m pip install -r wallet-pass/requirements.txt
   ```

6. Run the generator with your Issuer ID and private key file. It creates or updates the pass class and object through the Wallet API, then prints a signed save link:

   ```sh
   python3 wallet-pass/generate_add_to_wallet_link.py --issuer-id YOUR_ISSUER_ID --key-file /path/to/service-account.json
   ```

7. Open the generated link while signed in to an account authorized for the issuer. In Demo Mode, only issuer admins, developers, and test accounts can save passes.

The generator uses the service-account key locally to authenticate and sign the save link. It does not upload or store the key.
