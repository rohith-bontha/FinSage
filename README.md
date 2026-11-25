# FinSage — Financial Requirements Studio

FinSage keeps its original web interface and uses the Python multi-agent, RAG, storage, and document-generation backend from the user-authorized Software-eng-project- repository. The browser UI is served by FastAPI; retrieved evidence and draft outputs remain advisory and require human review.

## Run locally (Windows PowerShell)

Requires Python 3.11 or later.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. FastAPI documentation is available at http://127.0.0.1:8000/docs. The local JSON project store and SQLite vector index live under `data/`; runtime data and `.env` are excluded from Git.

## Project structure

- `index.html`, `styles.css`, `app.js` — FinSage frontend retained from the existing project
- `app/main.py` — FastAPI application and the reference project's API routes
- `app/finsage_adapter.py` — connects the retained FinSage screens to the reference agents and persistent project store
- `app/schemas.py` — validated project, evidence, requirement, risk, SDLC, and approval models
- `app/services/` — document extraction/masking, RAG/vector storage, LLM integration, requirements quality, compliance, risk, SDLC, evaluation, storage, SRS, and derived artefacts
- `app/prompts/` — prompt used for optional LLM requirement generation
- `requirements.txt` — Python dependencies
- `sample_data/` — sample source material
- `tests/` — reference backend test suite
- `docs/` — FinSage project documentation package

## Workflow

1. Enter the financial use case, project context, jurisdiction, SDLC factors, and role-specific interview answers.
2. Upload `.txt`, `.md`, `.csv`, `.json`, `.pdf`, or `.docx` evidence. The backend masks common sensitive number patterns, chunks the text, and indexes source evidence for retrieval.
3. FinSage retrieves evidence, generates traceable draft requirements, classifies them, checks quality, prepares risk and candidate RBI mappings, and derives project artefacts.
4. Review the evidence, requirements, clarification queue, control suggestions, SDLC alternatives, and gates. Record human decisions before adopting a baseline.
5. Edit and download the generated Markdown document pack. Use **Download SRS Word** for a locally generated Word SRS. Save project snapshots and export audit JSON from the UI.

The prototype uses local hashed embeddings and a persistent SQLite index without an API key. Optional OpenAI-compatible generation or embeddings can be configured through environment variables:

```text
LLM_API_KEY=your_authorized_provider_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
APP_DATA_DIR=data
VECTOR_DB_PATH=data/chroma
```

`OPENAI_API_KEY` is accepted as an alternative to `LLM_API_KEY`. The FinSage UI leaves external generation off until the user selects the consent option. Never place credentials in source files or committed project data.

## Backend API

The reference backend exposes RAG status, approved RBI source-register information, adaptive interview questions, evidence retrieval, requirement generation and approval, SDLC recommendation and approval, SRS Word generation, artefacts, evaluation, and project JSON export. The adapter adds the endpoints used by the retained UI: `/api/analyze`, `/api/interview-guides`, and `/api/project-snapshots`.

## Security and use limits

This is a local advisory prototype. It does not provide authenticated user accounts, enforceable RBAC/MFA, encrypted-at-rest project storage, or tamper-proof audit logs. Reviewer labels are not verified identities. RBI mappings are candidate suggestions from a limited versioned summary catalogue; they are not legal advice, a determination of applicability, or compliance certification. Review all sources and outputs with authorized business, security, privacy, architecture, operations, and compliance/legal stakeholders. Use only synthetic, anonymized, or institution-approved information.
