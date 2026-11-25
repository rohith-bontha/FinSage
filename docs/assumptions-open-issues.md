# Assumptions, Dependencies, and Open Issues

## Assumptions

- Initial use is an advisory requirements-engineering assistant for financial-sector projects.
- Humans retain approval authority for baselines, regulatory interpretations, high-risk decisions, SDLC selection, and production readiness.
- Institutions will provide approved, versioned policies and authoritative sources; the system cannot infer every applicable rule from a generic corpus.
- Sensitive data handling and permitted model endpoints are governed by institution policy.
- Generated documents remain drafts until explicit approval.

## Dependencies

- Identity provider and project-role source.
- Approved model endpoint and contractual/privacy controls.
- Secure document storage, retrieval index, structured database, workflow, and audit platform.
- Authoritative, licensed, jurisdiction-specific policy/regulatory knowledge corpus with owners and update process.
- Subject matter experts and representative anonymized evaluation cases.
- Security, privacy, compliance, architecture, and operations review capacity.

## Open issues

| ID | Question / decision | Needed from |
|---|---|---|
| OI-01 | Which country/jurisdictions and institution types are in scope? | Sponsor, compliance/legal |
| OI-02 | Which first case study/use case (e.g., onboarding, lending, payments, fraud, reporting)? | Product owner |
| OI-03 | What deployment environment, data residency, model provider, and model-data-use restrictions apply? | Architecture, security, privacy, procurement |
| OI-04 | What data classes may be processed, and what masking, retention, and deletion rules apply? | Privacy, security, records management |
| OI-05 | Which authoritative policies, controls, standards, and regulations will seed retrieval? Who maintains them? | Compliance, policy owners |
| OI-06 | Which integrations and file formats/languages must be supported first? | Architecture, operations, users |
| OI-07 | What availability, recovery, latency, throughput, and scale targets are required? | Operations, sponsor |
| OI-08 | What evaluation dataset, expert panel, thresholds, and release criteria will establish acceptable quality? | QA, model risk, domain owners |
| OI-09 | Who may approve requirement baselines, control mappings, SDLC choices, and production readiness? | Governance, sponsor |
| OI-10 | Which export formats and institutional document templates are required? | BA, records management |
