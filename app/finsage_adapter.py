"""API adapter that keeps the FinSage UI while using FinScope's Python agents."""
from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas import Project
from app.services.documents import chunk_text, extract_text, mask_sensitive
from app.services.generator import generate_evidence_drafts
from app.services.knowledge import approved_documents
from app.services.llm import enabled as llm_enabled, generate_requirements as generate_llm_requirements
from app.services.rag import RagConfigurationError


INTERVIEW_GUIDES = {
    "customer": ["What are you trying to complete, and what does success look like?", "What steps do you follow today, including exceptions?", "What information do you enter, view, or receive?", "What should happen when information is missing or incorrect?", "What would make you stop or distrust the process?"],
    "business": ["What business outcome and measurable target does this project support?", "Which users, products, regions, and workflows are in scope?", "What business rules, limits, exceptions, and approvals apply?", "Which existing systems or processes must remain compatible?", "What is explicitly out of scope?"],
    "security": ["Which data classes and threat scenarios are in scope?", "How are users authenticated, authorized, and reviewed?", "What security controls and testing evidence are required?", "What are the incident response and recovery expectations?", "Which security decisions require formal approval?"],
    "compliance": ["Which jurisdictions, entity types, products, and authoritative sources apply?", "What retention, reporting, audit, and approval obligations are known?", "Which policy or control owners can confirm applicability?", "What interpretations remain uncertain or need legal review?", "What evidence must be retained for audit?"],
    "operations": ["What availability, recovery time, and recovery point are required?", "Which integrations, batch windows, and operational dependencies exist?", "What monitoring, alerting, support, and escalation are needed?", "How are releases, rollback, and incident handling approved?", "What capacity and service level targets should be measured?"],
    "technical": ["What current architecture, APIs, data stores, and legacy constraints exist?", "What are the main interfaces, volumes, and failure modes?", "What performance, scale, and deployment targets are expected?", "Which environments, tools, and technical standards are mandated?", "What technical uncertainty needs a prototype or experiment?"],
}


def build_router(*, store, vector_store, requirements_agent, compliance_risk_agent, documentation_agent, governance_sdlc_agent, audit, record_agent_run):
    router = APIRouter()

    def get_snapshot(project: Project) -> dict:
        if isinstance(project.artefacts, dict) and project.artefacts.get("finsage_snapshot"):
            return project.artefacts["finsage_snapshot"]
        return {
            "id": project.id, "createdAt": project.created_at.isoformat(), "updatedAt": project.created_at.isoformat(),
            "project": {"name": project.functionality[:100], "domain": "Financial software", "description": project.functionality, "jurisdiction": "To be confirmed", "volatility": "medium", "risk": "high", "delivery": "continuous"},
            "analysis": {}, "recommendation": {}, "docs": [], "documents": [], "sources": [], "knowledgeBase": [], "approvals": [], "audit": project.audit_log,
        }

    def as_analysis(project: Project, use_llm: bool = False) -> dict:
        reqs = []
        for req in project.requirements:
            evidence = [item.model_dump(mode="json") for item in req.evidence]
            first = evidence[0] if evidence else {}
            reqs.append({
                "id": req.id, "statement": req.statement, "categories": [category.value for category in req.categories],
                "sourceId": first.get("document_id", "BRIEF"), "sourceName": first.get("document_name", "Project brief"),
                "sourceQuote": first.get("excerpt", req.statement), "sourceStakeholder": "Stakeholder to confirm",
                "businessJustification": req.business_justification, "priority": "High" if req.priority == "Must" else "Medium",
                "dependencies": req.dependencies, "assumptions": req.assumptions,
                "acceptanceCriteria": "\n".join(req.acceptance_criteria) or "TBD — define measurable stakeholder acceptance criteria.",
                "regulations": [item.model_dump(mode="json") for item in req.compliance_mappings],
                "riskLevel": req.risk_level, "confidence": req.confidence, "approvalStatus": req.approval_status,
                "approvalHistory": [], "qualityIssues": [],
            })
        issues = [{"id": item.id, "type": item.check, "severity": item.severity, "requirementIds": [item.requirement_id] if item.requirement_id else [], "message": item.message, "question": item.recommendation} for item in project.quality_issues]
        mappings = []
        for req in project.requirements:
            for mapping in req.compliance_mappings:
                citation = next((item for item in req.evidence if item.document_name == mapping.source_title), None)
                mappings.append({
                    "id": mapping.control_id, "requirementId": req.id, "categories": [category.value for category in req.categories],
                    "candidateControl": mapping.source_title, "status": "Candidate mapping · human review required",
                    "jurisdiction": mapping.jurisdiction, "gap": f"{mapping.applicability}. {mapping.rationale} Confirm applicability with authorized compliance/legal reviewers.",
                    "reviewerRole": "Compliance / Legal", "sourceEvidence": [{
                        "sourceId": citation.document_id if citation else "", "title": mapping.source_title,
                        "version": citation.source_version if citation else "Not specified", "jurisdiction": mapping.jurisdiction,
                        "effectiveDate": (citation.effective_date or "Not specified") if citation else "Not specified",
                        "evidence": citation.excerpt if citation else mapping.rationale,
                        "confidence": citation.relevance if citation else 0.4,
                    }],
                })
        sdlc = project.sdlc.model_dump(mode="json") if project.sdlc else {}
        evaluation = project.evaluation.model_dump(mode="json") if project.evaluation else {}
        ranked = [{"name": option["name"], "score": option["score"], "rationale": option["suitability"]} for option in sdlc.get("options", [])]
        workflow = [{
            "phase": phase["phase"], "activities": "; ".join(phase["activities"]), "roles": ", ".join(phase["roles"]),
            "deliverables": ", ".join(phase["deliverables"]), "entry": "Prior phase exit criteria met and accountable reviewers are identified.",
            "exit": phase["gate"], "controls": "Requirement traceability, secure development, privacy review, and documented human approval.",
        } for phase in sdlc.get("workflow", [])]
        clarification = [{"issueId": issue["id"], "requirementIds": issue["requirementIds"], "category": issue["type"], "question": issue["question"], "reviewerRole": "Business Analyst", "status": "Open"} for issue in issues]
        if not clarification:
            clarification = [{"issueId": f"CTX-{i+1}", "requirementIds": [], "category": "Project context", "question": question, "reviewerRole": "Project Sponsor", "status": "Open"} for i, question in enumerate(project.clarification_questions)]
        return {
            "requirements": reqs, "issues": issues, "complianceMappings": mappings,
            "risks": [{"id": risk.id, "requirementId": risk.requirement_id, "risk": risk.title, "category": risk.category, "riskLevel": risk.level, "impact": risk.level, "likelihood": risk.rationale, "owner": risk.owner_role, "mitigation": risk.mitigation, "status": risk.status} for risk in project.risks],
            "sdlc": {"selected": sdlc.get("recommended_sdlc", "To be determined"), "rationale": sdlc.get("justification", ""), "ranked": ranked,
                     "factors": sdlc.get("factors", []), "readiness": max(25, 100 - len(project.clarification_questions) * 8),
                     "missingFactors": project.clarification_questions, "status": "Provisional recommendation · human approval required"},
            "workflow": workflow, "clarifications": clarification,
            "agents": [{"name": run.agent, "status": run.status, "summary": run.output, "items": 0, "version": "1.0"} for run in project.agent_runs],
            "derivedArtefacts": json.loads(json.dumps(project.artefacts, ensure_ascii=False)),
            "metrics": {"extracted": len(reqs), "completeness": round(evaluation.get("measurable_acceptance_coverage", 0) * 100),
                        "traceability": round(evaluation.get("citation_coverage", 0) * 100),
                        "ambiguityFlags": sum("ambigu" in item["type"].lower() for item in issues),
                        "conflictFlags": sum("conflict" in item["type"].lower() for item in issues),
                        "candidateControlCoverage": round(evaluation.get("rbi_control_coverage", 0) * 100)},
            "llmUsed": use_llm, "llmModel": os.getenv("LLM_MODEL", "Evidence-only generation"),
            "knowledgeBaseVersion": "Versioned RBI catalogue and uploaded approved sources", "createdAt": project.created_at.isoformat(),
        }

    @router.get("/api/interview-guides")
    def interview_guides():
        return JSONResponse(INTERVIEW_GUIDES)

    @router.get("/api/health")
    def health():
        return JSONResponse({"status": "ok", "service": "finsage-reference-python-api", "storage": "local-json-and-vector-index", "llmConfigured": llm_enabled()})

    @router.post("/api/analyze")
    def analyze(payload: dict):
        context = payload.get("project") or {}
        description = str(context.get("description", "")).strip()
        if not str(context.get("name", "")).strip() or len(description) < 3:
            raise HTTPException(422, "Project name and a description of at least three characters are required.")
        project_id = uuid4().hex[:12]
        functionality = f"{context.get('name', 'Project')} — {context.get('domain', 'Financial software')}: {description}"
        documents = approved_documents()
        project_factors = "\n".join([
            f"Project name: {context.get('name', '')}", f"Financial use case: {context.get('domain', '')}",
            f"Jurisdiction: {context.get('jurisdiction', 'To be confirmed')}", f"Expected requirement change: {context.get('volatility', 'medium')}",
            f"Risk and criticality: {context.get('risk', 'high')}", f"Delivery cadence: {context.get('delivery', 'continuous')}",
            f"Technical complexity: {context.get('complexity', 'medium')}", f"Legacy constraints: {context.get('legacy', 'unknown')}",
            f"Verification rigor: {context.get('verification', 'high')}", f"Failure impact: {context.get('failureImpact', 'high')}",
            f"Stakeholder availability: {context.get('stakeholderAvailability', 'medium')}",
            f"Regulatory pressure: {context.get('regulatoryCriticality', context.get('regulatoryPressure', 'high'))}",
            f"Budget and schedule: {context.get('budgetSchedule', 'To be confirmed')}",
        ])
        documents.append({"id": "CTX-001", "name": "FinSage project context", "chunks": [chunk.__dict__ for chunk in chunk_text(mask_sensitive(project_factors))]})
        interview = context.get("interviewAnswers") or {}
        if interview:
            text = mask_sensitive("\n".join(f"{question}: {answer}" for question, answer in interview.items() if str(answer).strip()))
            answers = [str(answer) for answer in interview.values() if str(answer).strip()]
            unknowns = sum(any(term in answer.lower() for term in ["unknown", "not sure", "don't know", "not decided"]) for answer in answers)
            documents.append({"id": "DOC-001", "name": "Stakeholder interview", "answer_count": len(answers), "unknown_answer_count": unknowns, "chunks": [chunk.__dict__ for chunk in chunk_text(text)]})
        for source in payload.get("sources", []):
            name = str(source.get("filename") or source.get("name") or "source.txt")
            text = source.get("text", "")
            if source.get("base64"):
                try:
                    binary = base64.b64decode(source["base64"], validate=True)
                    if len(binary) > 5_000_000:
                        raise HTTPException(413, f"{name} exceeds the 5 MB limit.")
                    text = extract_text(name, binary)
                except (ValueError, TypeError) as exc:
                    raise HTTPException(422, f"Could not extract {name}.") from exc
            text = mask_sensitive(str(text))
            if text.strip():
                documents.append({"id": str(source.get("id") or f"DOC-{len(documents)+1:03d}"), "name": name, "version": source.get("version", "1.0"), "chunks": [chunk.__dict__ for chunk in chunk_text(text)]})
        for source in payload.get("knowledgeBase", []):
            if source.get("approved") and str(source.get("text", "")).strip():
                text = mask_sensitive(str(source["text"]))
                documents.append({"id": str(source.get("id") or f"KB-{len(documents)+1:03d}"), "name": str(source.get("title") or source.get("name") or "Approved knowledge source"), "version": source.get("version", "Unknown"), "jurisdiction": source.get("jurisdiction", "Not specified"), "effective_date": source.get("effectiveDate"), "source_url": source.get("authority"), "chunks": [chunk.__dict__ for chunk in chunk_text(text)]})
        project = Project(id=project_id, functionality=functionality, created_at=datetime.now(timezone.utc), documents=documents)
        try:
            indexed = vector_store.index(project.id, documents)
            evidence = vector_store.retrieve(project.id, functionality)
        except RagConfigurationError as exc:
            raise HTTPException(503, str(exc)) from exc
        if payload.get("useLlm") is True and not llm_enabled():
            raise HTTPException(503, "Optional external generation is not configured. Set LLM_API_KEY or OPENAI_API_KEY, then restart the server.")
        use_llm = payload.get("useLlm") is True and llm_enabled()
        if use_llm:
            try:
                candidates = generate_llm_requirements(functionality, evidence)
            except (RuntimeError, ValueError):
                candidates = generate_evidence_drafts(functionality, evidence)
        else:
            candidates = generate_evidence_drafts(functionality, evidence)
        requirements_agent.run(project, evidence, candidates)
        record_agent_run(project, requirements_agent.name, requirements_agent.responsibility, "Waiting for human review", f"Generated {len(project.requirements)} evidence-grounded draft requirements.")
        compliance_risk_agent.run(project)
        record_agent_run(project, compliance_risk_agent.name, compliance_risk_agent.responsibility, "Waiting for human review", "Prepared candidate mappings, risks, and traceability records.")
        documentation_agent.run(project)
        record_agent_run(project, documentation_agent.name, documentation_agent.responsibility, "Waiting for human review", "Generated the project artefact pack and evaluation measures.")
        project.sdlc = governance_sdlc_agent.run(project)
        record_agent_run(project, governance_sdlc_agent.name, governance_sdlc_agent.responsibility, "Waiting for human review", "Ranked and tailored SDLC workflow options for human review.")
        audit(project, "sources_masked_and_indexed", f"Indexed {indexed} source chunks after sensitive-pattern masking.")
        analysis = as_analysis(project, use_llm)
        docs = [{"id": key, "title": value.get("title", key.replace("_", " ").title()), "type": key.upper(), "description": key.replace("_", " ").title(), "content": json.dumps(value, indent=2, ensure_ascii=False)} for key, value in project.artefacts.items() if isinstance(value, dict) and "finsage_snapshot" not in key]
        snapshot = {"id": project.id, "createdAt": project.created_at.isoformat(), "updatedAt": datetime.now(timezone.utc).isoformat(), "project": context,
                    "analysis": analysis, "recommendation": analysis["sdlc"], "documents": docs, "docs": docs,
                    "sources": payload.get("sources", []), "knowledgeBase": payload.get("knowledgeBase", []), "approvals": [],
                    "audit": project.audit_log, "evaluation": analysis["metrics"], "rag": {**vector_store.configuration(), "indexedChunks": indexed}}
        project.artefacts["finsage_snapshot"] = snapshot
        store.save(project)
        return JSONResponse({"projectId": project.id, "analysis": analysis, "interviewGuides": INTERVIEW_GUIDES})

    @router.get("/api/project-snapshots")
    def list_snapshots():
        items = []
        for path in store.root.glob("*.json"):
            try:
                saved = Project.model_validate_json(path.read_text(encoding="utf-8"))
                if saved.artefacts.get("finsage_snapshot"):
                    snapshot = get_snapshot(saved)
                    items.append({"id": saved.id, "createdAt": snapshot["createdAt"], "updatedAt": snapshot.get("updatedAt", snapshot["createdAt"]), "name": snapshot["project"].get("name", saved.functionality), "domain": snapshot["project"].get("domain", "Financial software"), "recommendation": snapshot.get("recommendation", {}).get("primary", snapshot.get("recommendation", {}).get("selected", "Pending analysis")), "evaluation": snapshot.get("evaluation")})
            except Exception:
                continue
        return JSONResponse(sorted(items, key=lambda item: item["updatedAt"], reverse=True))

    @router.post("/api/project-snapshots")
    def create_snapshot(payload: dict):
        context = payload.get("project") or {}
        project = Project(id=uuid4().hex[:12], functionality=str(context.get("description") or context.get("name") or "FinSage project"), created_at=datetime.now(timezone.utc))
        snapshot = {**payload, "id": project.id, "createdAt": project.created_at.isoformat(), "updatedAt": datetime.now(timezone.utc).isoformat()}
        project.artefacts["finsage_snapshot"] = snapshot
        store.save(project)
        return JSONResponse(snapshot, status_code=201)

    @router.get("/api/project-snapshots/{project_id}")
    def read_snapshot(project_id: str):
        try:
            return JSONResponse(get_snapshot(store.get(project_id)))
        except KeyError as exc:
            raise HTTPException(404, "Project not found.") from exc

    @router.put("/api/project-snapshots/{project_id}")
    def update_snapshot(project_id: str, payload: dict):
        try:
            project = store.get(project_id)
        except KeyError as exc:
            raise HTTPException(404, "Project not found.") from exc
        previous = get_snapshot(project)
        updated_at = datetime.now(timezone.utc).isoformat()
        project.audit_log.append({"at": updated_at, "action": "snapshot_updated", "detail": "Saved project documents, approvals, and review history."})
        snapshot = {**payload, "id": project_id, "createdAt": previous.get("createdAt"), "updatedAt": updated_at, "audit": project.audit_log}
        project.artefacts["finsage_snapshot"] = snapshot
        store.save(project)
        return JSONResponse(snapshot)

    @router.get("/api/evaluation")
    def evaluation_summary():
        response = list_snapshots()
        saved_items = json.loads(response.body)
        return JSONResponse([{"id": item["id"], "name": item["name"], "metrics": item.get("evaluation")} for item in saved_items])

    return router
