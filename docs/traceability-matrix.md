# Requirements Traceability Matrix (Initial)

This matrix links system requirements to capabilities, verification evidence, and responsible review. Specific regulatory clauses and test IDs are intentionally TBD pending jurisdiction and design.

| Requirement IDs | Capability / artifact | Verification evidence | Reviewer |
|---|---|---|---|
| FR-01, FR-02, FR-03 | Project context and secure ingestion | Project setup, metadata, classification, and data-handling tests | BA, privacy, security |
| FR-04, FR-05, FR-08 | Structured extraction and classification | Gold-set precision/recall/F1; schema and provenance checks | BA, QA |
| FR-06, FR-07, FR-12 | Quality analysis and clarification | Labeled ambiguity/conflict dataset; reviewer usefulness assessment | BA, domain SMEs |
| FR-09, FR-10, FR-11 | Retrieval evidence and candidate mappings | Citation correctness, access-filter tests, unsupported-claim review | Compliance, security |
| FR-13, FR-20 | Document generation and export | Artifact completeness, ID preservation, cross-artifact consistency | BA, product owner |
| FR-14, FR-15, FR-16 | SDLC assessment and workflow | Expert-panel comparison, factor explanation and workflow review | PM, architect, security |
| FR-17, FR-18, FR-19 | Approval and audit trail | Role/gate tests, decision reconstruction, audit integrity test | Governance, audit |
| FR-21, FR-22 | Administration and evaluation | Configuration change log, repeatable evaluation report | Platform owner, model governance |
| NFR-01, NFR-02, NFR-12 | Security, privacy, AI safety | Threat model, penetration/adversarial tests, privacy review | Security, privacy |
| NFR-03, NFR-04, NFR-13 | Audit, explainability, source currency | Evidence trace, log review, stale-source/change tests | Audit, compliance |
| NFR-05 through NFR-11 | Reliability, performance, usability, interoperability, maintainability | Agreed SLO tests, recovery drills, user evaluation, API/version tests | Operations, QA, product |

At project baseline, expand this matrix to one row per requirement and link each to implementation component, test case, control source, evidence, owner, status, and approval.
