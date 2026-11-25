# FinSage Requirements Studio

A local full-stack project-planning tool for financial software teams. The website generates a heuristic SDLC recommendation and editable first-draft documents. A Node.js backend serves the app and saves/reopens project snapshots on the same computer.

## Run it

Requires Node.js 18 or newer. No third-party packages or API keys are needed.

1. In a terminal, change to this project folder.
2. Run `npm start`.
3. Open [http://127.0.0.1:3000](http://127.0.0.1:3000) in a browser.
4. Enter a project name, use case, and description; provide jurisdiction and delivery context where known.
5. Choose **Generate project analysis**, then **Save project** to persist it locally. Use the saved-project list to reopen it later.
6. Review and edit each document in the page. Download documents individually as Markdown, or download the combined pack.
7. Use **Print / save as PDF** to save a browser-rendered analysis summary.

The server binds to `127.0.0.1` by default. Project snapshots are stored in `data/projects.json` on this computer; that file is git-ignored. The project description and generated artifacts are stored as local JSON without encryption. Use sample or anonymized inputs only; do not store real customer, account, or regulated data in this prototype.

## Backend API

- `GET /api/health` — service status
- `GET /api/projects` — saved project summaries
- `POST /api/projects` — save a new project snapshot
- `GET /api/projects/:id` — load a saved project
- `PUT /api/projects/:id` — update its project details, recommendation, or documents

The API validates required fields and request size. Project analysis uses transparent browser-side heuristic rules; the backend does not call an LLM or make compliance determinations.

## Generated outputs

- Software Requirements Specification (SRS)
- SDLC recommendation, alternatives, and project workflow
- User stories and acceptance criteria
- Use cases
- Initial risk register
- Candidate compliance and control mapping
- Requirements Traceability Matrix (RTM)
- Assumptions, dependencies, and open issues

The recommendation uses transparent, lightweight rules based on supplied inputs. It is decision support, not an AI/LLM analysis, validated forecast, legal opinion, or compliance certification. The drafts are generic starting points and need review by project stakeholders.

## Files

- `index.html` — page structure and accessible controls
- `styles.css` — responsive visual design and print styles
- `app.js` — local recommendation logic and artifact generation
- `server.js` — dependency-free Node.js HTTP server and JSON project API
- `package.json` — start command and Node.js version requirement
- `data/projects.json` — created at runtime for local project persistence (not committed)
- `docs/` — initial project-specific planning document drafts
