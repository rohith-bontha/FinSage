# User Stories and Acceptance Criteria

| ID | Story | Acceptance criteria |
|---|---|---|
| US-01 | As a business analyst, I want to create a project with business context and jurisdiction so analysis uses the correct scope. | Required context fields are captured; unknowns are explicit; project access is restricted to assigned users. |
| US-02 | As an analyst, I want to upload interview notes and policies so requirements can be traced to source evidence. | Each source has owner, version/date, classification, and passage references; unsupported formats are reported. |
| US-03 | As a stakeholder, I want context-aware clarification questions so incomplete requirements can be resolved efficiently. | Each question identifies the source requirement and issue; stakeholder answers are retained with provenance. |
| US-04 | As a BA, I want requirements classified and checked for quality so defects are visible before baseline approval. | Requirements have stable IDs and required fields; ambiguity, conflict, duplication, and testability issues are flagged with evidence. |
| US-05 | As a compliance officer, I want candidate control mappings with citations so I can review applicability. | Mapping includes source/version/jurisdiction when known, rationale, gaps, confidence, and review status; no mapping is auto-approved. |
| US-06 | As a security reviewer, I want high-risk issues routed to me so they cannot be overlooked. | Configured severity and category rules create review tasks; status and decision appear in the audit record. |
| US-07 | As a project manager, I want ranked SDLC recommendations explained by project factors so I can make an informed choice. | Ranking exposes factor values and rationale, uncertainty, alternatives, and required human approval. |
| US-08 | As an analyst, I want SRS, stories, use cases, risk, compliance, and traceability artifacts generated together so they stay consistent. | Artifacts use shared IDs; generated content links back to sources; unresolved fields remain marked open. |
| US-09 | As an approver, I want to edit, accept, reject, or request regeneration so approved documents reflect accountable decisions. | Decision, actor, timestamp, prior version, and reason are retained; accepted versions are clearly identified. |
| US-10 | As an auditor, I want read-only access to artifact history and evidence so I can reconstruct how an output was produced. | Authorized audit view records sources, retrieved evidence, versions, edits, approvals, and exports without exposing unauthorized projects. |
