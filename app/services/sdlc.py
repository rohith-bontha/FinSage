from __future__ import annotations

import re

from app.schemas import Category, Requirement, SdlcFactor, SdlcOption, SdlcRecommendation, WorkflowPhase


UNKNOWN_ANSWER = re.compile(
    r"\b(?:no idea|i don't know|i do not know|don't know|do not know|not sure|unsure|unknown|not decided|not determined|not known|can't say|cannot say)\b",
    re.IGNORECASE,
)
INTERVIEW_LABEL = re.compile(
    r"(?i)(?<!\S)(business objective|users and roles|workflow and outcomes|business rules|exceptions|data and integrations|security and compliance|service levels and scale|delivery constraints|validation and rollout)\s*:"
)


def count_unknown_answers(answers: dict[str, str]) -> tuple[int, int]:
    """Count interview answers and those that explicitly say the answer is unknown."""
    values = [str(value).strip() for value in answers.values() if str(value).strip()]
    return len(values), sum(bool(UNKNOWN_ANSWER.search(value)) for value in values)


def infer_unknown_answers(interview_text: str) -> tuple[int, int]:
    """Recover answer counts for projects created before counts were stored."""
    labels = list(INTERVIEW_LABEL.finditer(interview_text))
    unknown_count = 0
    for index, label in enumerate(labels):
        end = labels[index + 1].start() if index + 1 < len(labels) else len(interview_text)
        answer = interview_text[label.end():end]
        unknown_count += bool(UNKNOWN_ANSWER.search(answer))
    return len(labels), unknown_count


def _requirement_ids(requirements: list[Requirement], categories: set[Category]) -> list[str]:
    return [requirement.id for requirement in requirements if categories & set(requirement.categories)]


def _factor(name: str, score: int, value: str, rationale: str, requirement_ids: list[str] | None = None) -> SdlcFactor:
    return SdlcFactor(name=name, score=score, value=value, rationale=rationale, requirement_ids=requirement_ids or [])


def _score(base: int, adjustments: list[tuple[bool, int]]) -> int:
    return max(0, min(100, base + sum(amount for applies, amount in adjustments if applies)))


def recommend(
    requirements: list[Requirement],
    project_context: str = "",
    interview_answer_count: int = 0,
    unknown_answer_count: int = 0,
    has_supporting_documents: bool = False,
) -> SdlcRecommendation:
    """Rank requested SDLC models from requirement signals without inventing project facts."""
    categories = {category for requirement in requirements for category in requirement.categories}
    source_text = " ".join([
        project_context,
        *(" ".join([requirement.statement, *(evidence.excerpt for evidence in requirement.evidence)]) for requirement in requirements),
    ]).lower()
    needs_review = sum(requirement.approval_status != "Approved" for requirement in requirements)
    measurable = sum(bool(requirement.acceptance_criteria) and not any("reviewer" in item.lower() for item in requirement.acceptance_criteria) for requirement in requirements)
    high_risk = sum(requirement.risk_level == "High" for requirement in requirements)
    security_or_compliance = {Category.SECURITY, Category.PRIVACY, Category.REGULATORY, Category.AUDIT}
    risk_ids = _requirement_ids(requirements, security_or_compliance)
    integration_ids = _requirement_ids(requirements, {Category.INTEGRATION, Category.DATA})
    stakeholder_ids = _requirement_ids(requirements, {Category.STAKEHOLDER, Category.USABILITY, Category.BUSINESS})
    controlled_requirements = any(term in source_text for term in ("formally approved", "requirements approval", "controlled change", "change-management", "change management"))
    formal_verification = any(term in source_text for term in ("verification and validation", "traceability between requirements", "unit testing", "integration testing", "system testing", "acceptance testing", "acceptance test"))
    explicit_acceptance = "acceptance criteria" in source_text

    unknown_interview = (
        interview_answer_count > 0
        and unknown_answer_count * 2 >= interview_answer_count
        and not has_supporting_documents
    )

    if unknown_interview:
        # Generated draft requirements must not turn unanswered interview
        # questions into apparent certainty. With no project documents to fill
        # the gaps, recommend a prototype as a way to learn and validate scope.
        stability_score = 2
        clarity_score = 2
        risk_score = 3
        complexity_score = 2
        early_prototype_score = 5
        time_score = 3
        involvement_score = 3
        change_score = 3
        iterative_score = 3
        risk_analysis_score = 3
        risk_ids = []
        integration_ids = []
        stakeholder_ids = []
    else:
        # Draft status alone means approval is outstanding; it is not evidence
        # that the project needs iterative delivery.
        stability_score = 4 if controlled_requirements else 2 if needs_review else 4
        clarity_score = 4 if measurable == len(requirements) or (formal_verification and explicit_acceptance) else 2 if measurable == 0 else 3
        risk_score = 5 if high_risk or risk_ids else 3
        complexity_score = 4 if integration_ids else 2
        early_prototype_score = 4 if clarity_score <= 2 or complexity_score >= 4 else 3
        time_score = 3
        involvement_score = 4 if stakeholder_ids else 3
        change_score = 3
        iterative_score = 4 if clarity_score <= 2 else 3
        risk_analysis_score = 5 if risk_score >= 5 or complexity_score >= 4 else 3

    factors = [
        _factor("Requirement stability", stability_score, "Needs validation" if needs_review else "Baseline approved", "Draft or unapproved requirements indicate that stability has not yet been demonstrated." if needs_review else "All requirements have an explicit approval status.", [requirement.id for requirement in requirements if requirement.approval_status != "Approved"]),
        _factor("Requirement clarity", clarity_score, "Not evidenced" if unknown_interview else "Low" if clarity_score <= 2 else "Moderate" if clarity_score == 3 else "High", "Half or more stakeholder answers were unknown; generated draft criteria do not establish validated clarity." if unknown_interview else "Measured from the presence of concrete, non-placeholder acceptance criteria.", [requirement.id for requirement in requirements if not requirement.acceptance_criteria or any("reviewer" in item.lower() for item in requirement.acceptance_criteria)] if not unknown_interview else []),
        _factor("Risk", risk_score, "Not evidenced" if unknown_interview else "High" if risk_score >= 5 else "Medium", "Stakeholder answers did not establish project-specific risk; confirm risks before selecting a controlled lifecycle." if unknown_interview else "Derived from stated high risk and security, privacy, regulatory, or audit classifications.", risk_ids),
        _factor("Complexity", complexity_score, "Not evidenced" if unknown_interview else "High" if complexity_score >= 4 else "Low", "Stakeholder answers did not establish project-specific integration or data complexity." if unknown_interview else "Integration and data-management requirements increase coordination and technical complexity.", integration_ids),
        _factor("Need for early prototype", early_prototype_score, "Likely" if early_prototype_score >= 4 else "Confirm with stakeholders", "Most interview answers were unknown; a prototype can help validate assumptions and discover requirements." if unknown_interview else "Unclear requirements or integration complexity make early learning and validation valuable."),
        _factor("Time constraints", time_score, "Not evidenced", "No schedule or deadline evidence is available in the generated requirements; confirm this with the project sponsor."),
        _factor("Customer involvement", involvement_score, "Not evidenced" if unknown_interview else "Evidenced" if stakeholder_ids else "Not evidenced", "Answers did not establish the level of customer availability for repeated feedback." if unknown_interview else "Derived only from business, stakeholder, or usability requirements; otherwise this must be confirmed.", stakeholder_ids),
        _factor("Frequency of changes", change_score, "Not evidenced", "Requirement documents do not establish the expected change rate; confirm with product and business stakeholders."),
        _factor("Need for iterative development", iterative_score, "Not evidenced" if unknown_interview else "Likely" if iterative_score >= 4 else "Confirm with stakeholders", "Interview answers did not establish expected feedback or change cycles." if unknown_interview else "Unclear requirements benefit from repeated review and validation cycles."),
        _factor("Need for risk analysis", risk_analysis_score, "Not evidenced" if unknown_interview else "High" if risk_analysis_score >= 5 else "Medium", "Project-specific risks were not established by the stakeholder answers." if unknown_interview else "Security/compliance concerns or complex integration warrant explicit risk analysis.", sorted(set(risk_ids + integration_ids))),
    ]

    stable = stability_score >= 4
    clear = clarity_score >= 4
    unclear = clarity_score <= 2
    high_risk_or_analysis = risk_score >= 5 or risk_analysis_score >= 5
    complex_project = complexity_score >= 4
    prototype_helpful = early_prototype_score >= 4
    iterative = iterative_score >= 4
    customer_available = bool(stakeholder_ids) and not unknown_interview
    time_pressure = time_score >= 4

    options = [
        SdlcOption(name="Waterfall", score=_score(42, [(stable, 25), (clear, 20), (not iterative, 8), (high_risk_or_analysis, 5), (unclear, -20)]), suitability="Best when requirements are stable, fully specified, and changes are controlled."),
        SdlcOption(name="V-Shape", score=_score(44, [(stable, 15), (clear, 15), (high_risk_or_analysis, 20), (formal_verification, 24), (unclear, -15)]), suitability="Best when each specification stage needs a linked verification and validation activity."),
        SdlcOption(name="Prototyping", score=_score(45, [(prototype_helpful, 26), (unclear, 18), (customer_available, 10), (complex_project, 8)]), suitability="Best for validating uncertain user needs, workflows, and interfaces before committing to a full build."),
        SdlcOption(name="RAD", score=_score(40, [(time_pressure, 25), (customer_available, 20), (iterative, 15), (high_risk_or_analysis, -10), (complex_project, -8)]), suitability="Best for time-boxed delivery with available users and modular, lower-risk scope."),
        SdlcOption(name="Spiral", score=_score(43, [(high_risk_or_analysis, 20), (complex_project, 12), (prototype_helpful, 12), (iterative, 8)]), suitability="Best when risk analysis, prototypes, and repeated risk-reduction cycles are central."),
        SdlcOption(name="Incremental", score=_score(46, [(iterative, 18), (complex_project, 12), (prototype_helpful, 10), (customer_available, 8), (time_pressure, 8)]), suitability="Best when value can be divided into validated, independently testable increments."),
        SdlcOption(name="Agile", score=_score(45, [(iterative, 22), (customer_available, 18), (prototype_helpful, 12), (unclear, 10), (high_risk_or_analysis, 3)]), suitability="Best for frequent feedback and evolving requirements, with planned governance for high-risk work."),
    ]
    # Formal verification evidence is a meaningful tie-breaker for high-risk
    # work; do not let a saturated score make Waterfall appear equally suitable.
    options.sort(
        key=lambda option: (
            option.score,
            option.name == "V-Shape" and formal_verification and high_risk_or_analysis,
        ),
        reverse=True,
    )
    choice = options[0].name
    factor_summary = ", ".join(
        f"{factor.name.lower()} needs validation" if factor.value == "Needs validation"
        else f"{factor.name.lower()} is {factor.value.lower()}"
        for factor in factors[:5]
    )
    return SdlcRecommendation(
        recommended_sdlc=choice,
        factors=factors,
        options=options,
        justification=(
            f"Half or more stakeholder interview answers were unknown and no project documents supplied the missing evidence. "
            f"Prototyping is recommended to validate assumptions and discover requirements before the lifecycle is selected. "
            f"{factor_summary}. Confirm the findings with stakeholders before approval."
            if unknown_interview
            else f"{choice} has the highest transparent score because {factor_summary}. Factors marked 'Not evidenced' are deliberately neutral and require stakeholder confirmation before the SDLC is approved."
        ),
        workflow=[
            WorkflowPhase(phase="Validate requirements", activities=["Resolve quality issues", "Confirm stability, time constraints, and expected changes", "Prioritise requirement baseline"], roles=["Business analyst", "Customer representative"], deliverables=["Validated requirements", "SDLC factor assessment"], gate="Stakeholder confirms project assumptions"),
            WorkflowPhase(phase="Plan the model", activities=["Review ranked SDLC options", "Plan risk analysis", "Define iteration or stage gates"], roles=["Project manager", "Architect", "Risk owner"], deliverables=["Approved SDLC decision", "Risk register"], gate="Engineering and business approval"),
            WorkflowPhase(phase="Develop and validate", activities=["Build planned scope", "Test against acceptance criteria", "Review feedback and risks"], roles=["Developers", "QA", "Customer representative"], deliverables=["Working increment or verified stage", "Test evidence"], gate="Quality and stakeholder acceptance"),
            WorkflowPhase(phase="Release and learn", activities=["Release approved scope", "Monitor outcomes", "Reassess requirement changes and risks"], roles=["Operations", "Product owner", "Project manager"], deliverables=["Release record", "Updated SDLC assessment"], gate="Release and change-control approval"),
        ],
    )
