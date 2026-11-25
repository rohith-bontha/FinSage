"""The staged multi-agent workflow used by FinScope.

Specialised agents extract requirements, assess compliance/risk, derive
artefacts, and recommend an SDLC. They never approve requirements or make a
legal determination; those decisions remain with human reviewers.
"""
from __future__ import annotations

from app.schemas import Project, Requirement, SdlcRecommendation
from app.services.generator import generate_evidence_drafts
from app.services.quality import analyse, clarification_questions
from app.services.sdlc import infer_unknown_answers, recommend
from app.services.compliance import analyse as analyse_compliance
from app.services.artefacts import build as build_artefacts
from app.services.evaluation import measure


class RequirementsAgent:
    """Extracts, classifies, and quality-checks evidence-grounded requirements."""

    name = "Requirements Agent"
    responsibility = "Requirement extraction, classification, traceability, and quality review"

    def run(self, project: Project, evidence: list[dict], requirements: list[Requirement] | None = None) -> list[Requirement]:
        project.requirements = requirements or generate_evidence_drafts(project.functionality, evidence)
        project.quality_issues = analyse(project.requirements)
        project.clarification_questions = clarification_questions(project.quality_issues)
        return project.requirements


class ComplianceRiskAgent:
    """Maps prototype RBI controls and raises reviewable risk entries."""

    name = "Compliance & Risk Agent"
    responsibility = "RBI control mapping, risk register generation, and traceability"

    def run(self, project: Project) -> None:
        project.risks, project.traceability = analyse_compliance(project.requirements)


class DocumentationAgent:
    """Produces derived artefacts without inventing uncited requirements."""

    name = "Documentation Agent"
    responsibility = "SRS, user-story, use-case, traceability, risk, and open-issue artefacts"

    def run(self, project: Project) -> None:
        project.evaluation = measure(project)
        project.artefacts = build_artefacts(project)


class GovernanceSdlcAgent:
    """Assesses risk/control signals and produces a transparent SDLC advisory."""

    name = "Governance & SDLC Agent"
    responsibility = "Risk and control assessment, SDLC ranking, and approval-gate planning"

    def run(self, project: Project) -> SdlcRecommendation:
        # Requirements are retrieved from the most relevant chunks, while SDLC
        # evidence (for example delivery gates and test strategy) can be in a
        # different stakeholder-answer chunk. Include the complete masked
        # project evidence without inventing any new project facts.
        project_context = " ".join(
            chunk.get("text", "")
            for document in project.documents
            for chunk in document.get("chunks", [])
        )
        interview_document = next(
            (document for document in project.documents if document.get("id") == "DOC-001"),
            None,
        )
        interview_text = " ".join(
            chunk.get("text", "") for chunk in (interview_document or {}).get("chunks", [])
        )
        if interview_document and "answer_count" in interview_document:
            answer_count = int(interview_document.get("answer_count", 0))
            unknown_answer_count = int(interview_document.get("unknown_answer_count", 0))
        else:
            answer_count, unknown_answer_count = infer_unknown_answers(interview_text)
        has_supporting_documents = any(
            document.get("id") != "DOC-001"
            and not str(document.get("id", "")).startswith("KB-")
            and any(chunk.get("text", "").strip() for chunk in document.get("chunks", []))
            for document in project.documents
        )
        project.sdlc = recommend(
            project.requirements,
            project_context,
            interview_answer_count=answer_count,
            unknown_answer_count=unknown_answer_count,
            has_supporting_documents=has_supporting_documents,
        )
        return project.sdlc
