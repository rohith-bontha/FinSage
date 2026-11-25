# Candidate Compliance and Control Mapping

This is a **control discovery template**, not a jurisdiction-specific compliance determination. The problem statement did not specify country, institution type, product, data residency, or applicable rulebook. Compliance/legal officers must select authoritative current sources, confirm applicability, and approve mappings before implementation or reliance.

| Area | Candidate system requirement/control | Evidence to retain | Reviewer |
|---|---|---|---|
| Privacy and personal data | Minimize, classify, mask, restrict use, set retention/deletion, and record processing purpose | Data inventory, flows, masking tests, retention configuration, approvals | Privacy/legal |
| Information security | Least privilege, MFA/SSO, encryption, key management, secure development, vulnerability management | Access reviews, configurations, test results, change records | Security |
| Outsourcing / third-party risk | Assess model, cloud, storage, and retrieval providers; document location, use, resilience, subcontractors, exit plan | Due diligence, contracts, data-flow and exit plans | Third-party risk, legal |
| Operational resilience | Define availability, backup, recovery, incident response, rollback, and service dependency controls | BCP/DR tests, runbooks, incident records | Operations, resilience |
| Audit and recordkeeping | Preserve attributable inputs, evidence, versions, approvals, changes, and exports under approved retention | Audit-event samples, retention schedule, access logs | Audit, compliance |
| Model/AI governance | Inventory models/agents, validate intended use, monitor quality/drift, manage changes and human oversight | Model cards, evaluations, approvals, monitoring reports | Model risk, governance |
| Financial crime / customer controls | Where relevant, capture requirements for KYC, fraud monitoring, sanctions screening, and escalation | Approved use-case mapping and test evidence | Financial crime compliance |
| Payments / transaction integrity | Where relevant, include authorization, limits, reconciliation, idempotency, fraud, dispute and resilience controls | Test cases, reconciliation evidence, control mappings | Payments, security |
| Accessibility and consumer outcomes | Where relevant, review accessible interaction, explainability, complaint handling, and adverse-impact safeguards | User tests, accessibility review, complaint process | Product, conduct risk |
| Secure AI interaction | Treat documents as untrusted; prevent prompt injection, data exfiltration, unauthorized tool actions, and cross-project leakage | Threat model, red-team tests, tool allowlist, audit | Security, AI governance |

For each eventual regulation/control, add: authority and exact citation; jurisdiction; effective date; applicability rationale; mapped requirement IDs; implementation owner; evidence artifact; test method/result; reviewer and approval date; exceptions/remediation. Keep unresolved items open and visible.
