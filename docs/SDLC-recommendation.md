# SDLC Recommendation and Project Workflow

## Recommendation

**Recommended starting approach: hybrid Agile + DevSecOps with V-Model verification and approval gates for regulated/high-impact deliverables.** This is a reasoned initial recommendation based on the problem statement, not a calculated prediction from validated project inputs. The product combines evolving AI capabilities and stakeholder workflows with sensitive financial data, auditability, security obligations, and formal review needs. Iterative delivery supports changing requirements; DevSecOps integrates security and deployment controls; V-Model practices provide explicit verification, validation, and traceability for critical requirements.

**Confidence:** Provisional; no project-specific jurisdiction, budget, team, deployment target, or volatility data was supplied. Reassess after discovery. Alternatives: Spiral if major technical/security uncertainty dominates; V-Model if scope is stable and formal assurance dominates; Agile alone is insufficient for regulated gates; Waterfall is a weaker fit where AI/UX requirements will evolve.

## Decision factors to confirm

| Factor | Initial reading | Effect |
|---|---|---|
| Regulatory and audit criticality | High | Formal evidence, approvals, traceability, and change control |
| Security/privacy risk | High | Threat modeling, secure design, continuous testing, controlled data |
| Requirement volatility | Medium-high | Short iterations and frequent stakeholder validation |
| Technical uncertainty | Medium-high (agent/RAG quality) | Prototype and evaluate early; consider Spiral risk loops |
| Verification needs | High | Map requirements to tests and formal validation gates |
| Legacy/integration constraints | Unknown | Discovery spike and integration testing required |
| Continuous delivery need | Desired, not confirmed | Automate pipelines with staged release approvals |
| Failure impact | Potentially high | Risk-based testing and human production readiness approval |

## Proposed workflow

| Phase | Activities | Accountable roles | Deliverables and gate |
|---|---|---|---|
| 0. Governance and discovery | Set use case, jurisdictions, data classification, stakeholders, success metrics, and approved sources | Sponsor, BA, compliance, security, privacy | Scope brief, stakeholder map, data-flow draft; gate: sponsor and control owners accept discovery scope |
| 1. Backlog and requirements | Interviews, source ingestion, extraction, clarification, conflict resolution, classification | BA/product owner, domain SMEs, AI assistant | SRS, stories, use cases, RTM, open issues; gate: authorized requirement baseline |
| 2. Architecture and risk | Threat modeling, privacy impact, model/provider assessment, architecture, retrieval and access design | Architect, security, privacy, compliance | Architecture, threat/risk register, control mappings; gate: architecture/security review |
| 3. Iterative implementation | Build thin vertical slices; peer review; unit/integration tests; static/dependency/secrets checks | Engineering, QA, security champion | Versioned increments, code review, pipeline evidence; gate: quality and security checks pass |
| 4. Verification and validation | Requirement-linked tests, retrieval/citation evaluation, adversarial/prompt-injection tests, bias checks, performance and recovery tests, user acceptance | QA, security, BA, business users | Test evidence, defects, evaluation report, updated RTM; gate: severity thresholds met and owners sign off |
| 5. Release readiness | Change approval, access review, data/retention verification, operational runbooks, rollback rehearsal | Operations, release manager, compliance, security | Release package, approvals, rollback and incident plans; gate: human production-readiness approval |
| 6. Operate and improve | Monitor quality/drift, audit changes, review incidents, update sources/rules, reassess risks | Operations, model governance, compliance, product | Monitoring reports, audit records, updated backlog; gate: periodic governance review |

## Required controls throughout
Maintain requirement-to-test-to-control traceability; version prompts/models/rules/knowledge; isolate project context; allowlist retrieval sources and agent tools; screen untrusted instructions; use synthetic or anonymized evaluation data where feasible; require human approval for legal/control decisions and SDLC adoption; record evidence and reviewer decisions. Release cadence and numerical gates remain to be agreed.
