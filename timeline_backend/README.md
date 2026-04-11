# Timeline Generator Backend API

A production-ready FastAPI backend integrating HuggingFace transformers (`dslim/bert-base-NER`) to extract historical actors, occurrences, and explicit dates into a chronological structured timeline JSON.

## Folder Structure

```text
timeline_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI routing & Model execution loop
│   ├── schemas.py                # Pydantic validation (Request/Response)
│   └── services/
│       ├── __init__.py
│       ├── extractor.py          # HuggingFace NLP pipeline wrapper
│       └── date_parser.py        # Date resolution utilities
├── requirements.txt
└── README.md
```

## Setup & Running Locally

1. **Install dependencies**:
   Ensure you are in the `timeline_backend` root directory.
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the FastAPI Server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *Note: On first boot, the server will pause to download the pre-trained HuggingFace BERT model (~400MB).*

3. **Check interactive Documentation**:
   Navigate to `http://localhost:8000/docs` in your browser to view the interactive Swagger UI.

## API Documentation

### `POST /api/v1/extract`

Extracts structured events.

**Request:**
```json
{
  "text": "The American Civil War effectively ended when Robert E. Lee surrendered to Ulysses S. Grant on April 9, 1865. President Abraham Lincoln was assassinated shortly after on April 14, 1865.",
  "base_date": null
}
```

**Response (`200 OK`):**
```json
{
  "events": [
    {
      "date": "1865-04-09",
      "description": "The American Civil War effectively ended when Robert E. Lee surrendered to Ulysses S. Grant on April 9, 1865.",
      "actor": "Robert E. Lee",
      "location": null
    },
    {
      "date": "1865-04-14",
      "description": "President Abraham Lincoln was assassinated shortly after on April 14, 1865.",
      "actor": "Abraham Lincoln",
      "location": null
    }
  ]
}
```
