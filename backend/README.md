# App Relation Backend

Python backend for importing mobile AI recognition results, deduplicating functional pages, and serving app graph data.

## Local Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Create a local PostgreSQL database named `app_relation`, then enable pgvector through the dev endpoint:

```powershell
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`, then call:

- `POST /api/imports/init-db`
- `POST /api/imports/scan-folder`
- `GET /api/graph/{app_id}`
- `POST /api/replay/analyze`

## Folder Flow

The mobile script saves screenshots and AI JSON under a local folder. The backend scans JSON files from `IMPORT_INBOX_DIR` or a request-specific folder.

Recommended layout:

```text
backend/inbox/demo-scan/
  ai_result.json
  screenshots/
    home.png
    search.png
```

Import request:

```json
{
  "folder": "./inbox/demo-scan"
}
```

## AI JSON Shape

See `examples/ai_result_example.json`.

Important fields:

- `app`: app identity. `package_name` is the stable key for top app coverage.
- `scan`: one run from a device/script/model combination.
- `pages`: AI-recognized page instances. Keep raw OCR, AI summary, normalized layout, widgets, and screenshot path.
- `edges`: transitions discovered by tap, long press, swipe, back, or deep link.

`structure_hash` can be supplied by the script. If omitted, the backend derives it from stable page structure fields. This is the functional page dedupe key: dynamic content such as video title, product name, or feed item text should not dominate the hash.

## Page Hash Guidance

Use multiple hashes for different purposes:

- `screenshot_hash`: raw screenshot file sha256. Good for asset integrity, not good for page dedupe.
- `visual_hash`: perceptual image hash. Useful for similar screen detection.
- `structure_hash`: normalized layout and widget semantics. Primary key for functional page dedupe.
- `route_hash`: native activity/web URL/deeplink route if available. Useful signal, not always 1:1 with graph nodes.

For apps like Douyin/TikTok, many video screenshots can have different `screenshot_hash` values while sharing one `structure_hash` for the same video detail page structure.

## pgvector

The schema includes `embedding_records` with a `Vector(1536)` column. Store embeddings for:

- canonical page summaries
- widget semantic descriptions
- OCR text chunks
- replay/user URL descriptions

If the embedding model dimension changes, create a migration before changing the vector column dimension.

