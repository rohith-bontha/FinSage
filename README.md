# FinSage Requirements Studio

A browser-based project-planning tool for financial software teams. It generates a heuristic SDLC recommendation and an editable first-draft document pack from a project brief.

## Run it

No build step, package installation, account, or backend is required.

1. Open `index.html` in a current desktop or mobile browser.
2. Enter a project name, use case, and description; provide jurisdiction and delivery context where known.
3. Choose **Generate project analysis**.
4. Review and edit each document in the page. Download documents individually as Markdown, or download the combined pack.
5. Use **Print / save as PDF** to save a browser-rendered analysis summary.

For local hosting, serve this folder with any static file server. Keep `index.html`, `styles.css`, and `app.js` together.

## Generated outputs

- Software Requirements Specification (SRS)
- SDLC recommendation, alternatives, and project workflow
- User stories and acceptance criteria
- Use cases
- Initial risk register
- Candidate compliance and control mapping
- Requirements Traceability Matrix (RTM)
- Assumptions, dependencies, and open issues

The recommendation uses transparent, lightweight rules based on supplied inputs. It is decision support, not an AI/LLM analysis, validated forecast, legal opinion, or compliance certification. The drafts are generic starting points and need review by project stakeholders. No project data is sent to a server; generated drafts and edits remain in the open browser tab until downloaded. Closing or refreshing the page clears the current project.

## Files

- `index.html` — page structure and accessible controls
- `styles.css` — responsive visual design and print styles
- `app.js` — local recommendation logic and artifact generation
- `docs/` — initial project-specific planning document drafts
