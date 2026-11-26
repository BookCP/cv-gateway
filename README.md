# Native Google Wallet profile pass

This folder contains a native Google Wallet Generic pass design. It sets the forest-green background, uses the CV portrait as the hero image, provides a simple “A” logo, and places the portfolio URL in a QR code. The contact fields and links come from the CV and profile.

Google Wallet displays a hero image below the barcode and pass fields. This custom image replaces the generic category artwork. Wallet still uses its own card layout; the API controls the color, images, barcode, title, and data fields.

## Before creating the pass

1. Create a Google Wallet API Issuer account and note its numeric Issuer ID.
2. Create a Google Cloud service account, enable the Google Wallet API, and authorize the service account in Google Wallet Console.
3. Download its JSON key to a private folder outside this repository.
4. Upload this `wallet-pass` folder to the public `cv-gateway` GitHub repository so the two image URLs in `pass-design.json` are available over HTTPS.
5. Install the one Python dependency from this folder:

   ```sh
   python3 -m pip install -r wallet-pass/requirements.txt
   ```

6. Generate the signed Add to Google Wallet link locally:

   ```sh
   python3 wallet-pass/generate_add_to_wallet_link.py --issuer-id YOUR_ISSUER_ID --key-file /path/outside/repo/service-account.json
   ```

7. Open the generated link on your phone while signed in to an account authorized for the issuer. In Demo Mode, Google limits saving to the issuer's admin/developer users and test accounts. Publishing to other users requires Google's publishing access.

Keep the service-account JSON key outside the repository and never upload it to GitHub. The generator prints the signed save link; it does not save credentials or contact Google APIs itself.
