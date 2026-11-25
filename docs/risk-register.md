# Initial Risk Register

Likelihood and impact are preliminary qualitative estimates for planning and require owner review.

| ID | Risk | Likelihood / impact | Mitigation and evidence | Owner |
|---|---|---|---|---|
| R-01 | Hallucinated or unsupported requirements/mappings | Medium / High | RAG from allowlisted sources, citations, unsupported-claim flags, rule checks, sampling and expert evaluation | AI governance, BA |
| R-02 | Prompt injection in stakeholder files or retrieved content | Medium / High | Treat content as untrusted data, isolate instructions, restrict tools, sanitize inputs, adversarial tests, audit | Security |
| R-03 | Exposure of sensitive financial or personal data | Medium / Critical | Data minimization, classification, masking, encryption, access controls, approved endpoints, retention/deletion controls | Privacy, security |
| R-04 | Incorrect jurisdiction or stale regulatory source | Medium / High | Version/effective-date metadata, jurisdiction confirmation, change monitoring, human legal/compliance review | Compliance |
| R-05 | Automation bias leads to unreviewed recommendations | Medium / High | Clear draft status, mandatory gates, alternatives and uncertainty, reviewer accountability, training | Product, governance |
| R-06 | Bias or inconsistent treatment across user groups/cases | Medium / High | Representative anonymized evaluation, subgroup review, feedback and correction tracking | Model governance |
| R-07 | Agent coordination produces contradictory or lost decisions | Medium / Medium | Shared typed artifact schema, orchestration state, provenance, validation, replayable audit | Engineering |
| R-08 | Legacy-system constraints are missed | Medium / High | Source inventory, integration discovery, SME interviews, dependency register, integration testing | Architecture |
| R-09 | Knowledge base access or retrieval leaks across projects | Low-medium / Critical | Tenant/project filters enforced server-side, negative access tests, retrieval allowlists, monitoring | Security |
| R-10 | SDLC ranking is miscalibrated or overstates precision | Medium / Medium | Transparent factors, provisional ranking, expert-panel evaluation, recalibration, human adoption decision | Project governance |
| R-11 | Audit history is incomplete or tampered with | Low-medium / High | Immutable or protected logging, access separation, retention policy, audit testing | Operations, audit |
| R-12 | Model/provider, cost, or latency changes disrupt service | Medium / Medium | Provider abstraction, version pinning, performance/cost monitoring, fallback and rollback plans | Platform owner |

Escalate any critical risk through the institution's existing risk governance process. Risk acceptance belongs to authorized owners.
