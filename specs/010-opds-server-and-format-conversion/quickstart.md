# Quickstart: 010 OPDS 1.2/2.0 Feed Server & Format Conversion Engine

## 1. Connecting an E-Reader via OPDS

### In KOReader (Kindle, Kobo, Android):
1. Tap the Top Menu ➔ **Search / OPDS Catalog**.
2. Tap **Add catalog**.
3. Enter Name: `xBookLibrary`
4. Enter URL: `http://<your-pc-ip>:8000/opds` (e.g., `http://192.168.1.50:8000/opds`).
5. Tap **Connect**.
6. Browse your collection by All Books, Recent, or Categories, and tap any book to download directly!

### In Moon+ Reader (Android):
1. Open the drawer ➔ **Net Library**.
2. Tap **Add new catalog**.
3. URL: `http://<your-pc-ip>:8000/opds`
4. Tap **Save** and start downloading books wirelessly.

---

## 2. Converting a Book via API

```bash
# Convert a legacy MOBI or CBZ book into EPUB
curl -X POST http://127.0.0.1:8000/api/convert \
  -H "Content-Type: application/json" \
  -d '{"book_id": 1, "source_format": "MOBI", "target_format": "EPUB"}'

# Poll conversion status
curl http://127.0.0.1:8000/api/convert/jobs/<job_id>
```
