# Quickstart Guide: Send-to-Device & Wireless E-Reader Sync

## 1. Setting up "Send to Kindle"
1. Open **Settings** -> **Device & SMTP Configuration** in xBookLibrary.
2. Enter your SMTP details (e.g. Host: `smtp.gmail.com`, Port: `587`, Sender: `your_email@gmail.com`, App Password).
3. In your Amazon Account under *Manage Your Content and Devices* -> *Preferences* -> *Personal Document Settings*, add `your_email@gmail.com` to the **Approved Personal Document E-mail List**.
4. In xBookLibrary, click **Add Device** -> Choose **Kindle** -> enter your Kindle's address (`username@kindle.com`).
5. Select any book in your library -> Click **Send to Device** -> Select your Kindle. The book will be dispatched as an EPUB!

## 2. Setting up Wireless Kobo Sync
1. In xBookLibrary **Settings** -> **Devices**, click **Add Device** -> Choose **Kobo**.
2. Copy the generated Kobo Sync URL:
   `http://<your-server-ip>:8000/api/sync/kobo/<auth_token>`
3. Plug your Kobo e-reader into your computer once, edit `.kobo/Kobo/Kobo eReader.conf`, and set:
   ```ini
   [OneStoreServices]
   api_endpoint=http://<your-server-ip>:8000/api/sync/kobo/<auth_token>
   ```
4. Eject your Kobo. Whenever your Kobo connects to Wi-Fi and clicks "Sync", your books will sync wirelessly and reading progress will sync back to xBookLibrary!

## 3. Setting up KOReader Wireless Sync (Kosync)
1. In KOReader on your e-reader, open the top menu -> **Tools** -> **Progress sync (Kosync)**.
2. Under **Custom server**, enter `http://<your-server-ip>:8000/api/sync/koreader`.
3. Register or sign in with your chosen username and password.
4. Reading progress will automatically sync seamlessly across all your devices running KOReader!
