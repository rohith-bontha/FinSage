# Use Cases

## UC-01: Gather and validate requirements

**Primary actors:** Business analyst, stakeholder. **Preconditions:** Project exists; user has project access; permitted sources are configured. **Trigger:** Analyst begins a discovery session or imports materials.

**Main flow:** (1) Analyst selects a project and source. (2) System classifies source and applies configured sensitive-data handling. (3) Extraction agent proposes atomic, categorized requirements with source passages. (4) Quality agents flag ambiguity, omissions, conflicts, duplicates, and weak acceptance criteria. (5) System proposes clarifying questions. (6) Stakeholder answers; analyst edits requirements. (7) System updates evidence and traceability. (8) Authorized approver reviews and baselines the requirements.

**Alternates/exceptions:** Sensitive data cannot be safely handled: block or quarantine and notify authorized user. Source is unreadable: report failure without inventing content. Sources conflict: preserve both claims and create an issue. Low evidence/confidence: mark unsupported and route for review. Approval rejected: return to clarification/editing; preserve decision history.

**Postconditions:** Draft or approved version exists with provenance, unresolved issues, and review history.

## UC-02: Review candidate compliance mapping

**Primary actors:** Compliance/legal officer, security reviewer. **Preconditions:** Requirements and authorized, versioned knowledge sources exist.

**Main flow:** (1) System retrieves applicable candidate sources using configured jurisdiction/context. (2) System proposes mappings and rationale with citations, source versions, effective dates when available, confidence, and gaps. (3) Reviewer inspects evidence. (4) Reviewer accepts, edits, rejects, or requests further evidence. (5) System records the decision and links it to affected requirements.

**Exceptions:** Jurisdiction or source currency is unknown: display unresolved applicability and do not claim compliance. Source access fails: mark mapping incomplete. High-impact legal interpretation: require designated legal/compliance approval.

**Postconditions:** Mapping remains candidate or has a named human review decision; audit history is preserved.

## UC-03: Generate project SDLC recommendation and deliverables

**Primary actors:** Project manager, architect, BA, security/compliance approvers. **Preconditions:** Project context and sufficient validated requirements are available.

**Main flow:** (1) System derives decision factors and marks unknowns. (2) System ranks candidate SDLC approaches and explains trade-offs. (3) System drafts phases, activities, roles, deliverables, tests, gates, and controls. (4) System generates linked SRS and supporting artifacts. (5) Project manager and designated reviewers revise and approve. (6) System versions and exports the approved package.

**Exceptions:** Insufficient inputs: return a provisional result with missing factors and questions. Conflicting factors: show alternatives and trade-offs. No human approval: retain recommendation as draft. Changed requirements: identify potentially impacted artifacts and request revalidation.

**Postconditions:** Versioned draft or approved recommendation and artifacts, with traceability and review record.
