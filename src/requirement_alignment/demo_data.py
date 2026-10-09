"""Canonical deterministic model-benchmark workflow for DEMO mode and tests."""

from datetime import datetime, timezone
from uuid import NAMESPACE_URL, UUID, uuid5

from requirement_alignment.models import (
    AcceptanceCriterion, AnalysisItem, ClarificationQuestion, CompletionEvaluation,
    CompletionStatus, CriterionEvaluation, CriterionStatus, Deliverable, DiffCategory,
    ExecutionPlan, FieldType, ImpactAnalysis, Metric, MetricOperator, Priority,
    QuestionStatus, RawRequirement, RequirementAnalysis, RequirementChange,
    RequirementDiff, RequirementDiffEntry, RequirementField, RequirementVersion,
    RiskItem, Task, TaskImpact, TaskStatus, WorkflowState,
)
from requirement_alignment.services import evaluate_completion, revise_execution_plan


def fixture_id(name: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"requirement-alignment.example/{name}")


NOW = datetime(2026, 9, 24, 8, 0, tzinfo=timezone.utc)
STAKEHOLDER_CHANGE_TEXT = (
    "豆包 1.5 快下架了，不需要继续测试。下周跑项目测试集并继续补充测试集，"
    "最后对 Top 2 做 Final Validation。"
)

RAW_REQUIREMENT = RawRequirement(
    id=fixture_id("raw"), title="模型能力评测",
    description="测试不同模型的能力评分，看看哪个模型比较适合我们的业务。",
    submitted_by="业务负责人", source="stakeholder interview",
    status=WorkflowState.NEEDS_CLARIFICATION, created_at=NOW,
)

_GAPS = [
    ("Which candidate models should be tested?", "candidate_models"),
    ("Which capability should be evaluated first?", "scope"),
    ("Which dataset should be used?", "dataset"),
    ("Is the test generic or project-specific?", "scope"),
    ("How should response quality be scored?", "metrics.quality"),
    ("Does model cost affect selection?", "metrics.cost"),
    ("Does response latency affect selection?", "metrics.latency"),
    ("What final deliverable is required?", "expected_outputs"),
    ("How will the final recommendation be determined?", "acceptance_criteria"),
]

ANALYSIS = RequirementAnalysis(
    id=fixture_id("analysis"), raw_requirement_id=RAW_REQUIREMENT.id,
    confirmed_information=[
        AnalysisItem(description="Multiple models need to be compared", affected_fields=["scope"]),
        AnalysisItem(description="The purpose is to support model selection", affected_fields=["objective"]),
    ],
    missing_information=[AnalysisItem(description=text, affected_fields=[field]) for text, field in _GAPS],
    assumptions=[
        AnalysisItem(description="All active candidates can be called through a consistent interface"),
        AnalysisItem(description="Test data can be used without exposing sensitive production data"),
    ],
    ambiguities=[
        AnalysisItem(description="Model capability could mean a generic skill or project performance"),
        AnalysisItem(description="Suitable has no defined trade-off between quality, latency, and cost"),
    ],
    risks=[RiskItem(
        description="Results will not be comparable without a frozen dataset and scoring rubric",
        likelihood=Priority.HIGH, impact=Priority.HIGH,
        mitigation="Freeze cases, prompts, settings, and scoring before execution",
    )], analyzed_at=NOW,
)

_ANSWERS = [
    "Test currently available candidates: GPT-5, Claude Sonnet, Gemini Pro, and Doubao 1.5",
    "Focus first on Brief Understanding",
    "Use a frozen 100-case generic Brief Understanding set",
    "Run a generic test first; project-specific validation is out of scope for V1",
    "Blind-score correctness, completeness, and instruction following",
    "Yes; estimate normalized token cost",
    "Yes; compare P95 end-to-end latency",
    "Produce benchmark results, a model comparison, and a recommendation report",
    "Use weighted quality (60%), latency (20%), and cost (20%)",
]
CLARIFICATION_QUESTIONS = [
    ClarificationQuestion(
        id=fixture_id(f"question-{index}"), analysis_id=ANALYSIS.id,
        question=gap[0], rationale=f"Required to define {gap[1]}", target_field=gap[1],
        priority=Priority.HIGH, status=QuestionStatus.ANSWERED,
        answer=_ANSWERS[index - 1], answered_by="业务负责人", answered_at=NOW,
    )
    for index, gap in enumerate(_GAPS, start=1)
]

QUALITY_METRIC = Metric(
    id=fixture_id("metric-quality"), name="Quality pass rate",
    description="Share passing the frozen Brief Understanding rubric",
    measurement_method="Blind reviewer pass count divided by total cases",
    target_operator=MetricOperator.GTE, target_value=0.8, unit="ratio",
)
LATENCY_METRIC = Metric(
    id=fixture_id("metric-latency"), name="P95 latency",
    description="95th percentile end-to-end latency",
    measurement_method="Repeated runs in the same environment",
    target_operator=MetricOperator.LTE, target_value=8, unit="seconds",
)
COST_METRIC = Metric(
    id=fixture_id("metric-cost"), name="Normalized cost",
    description="Token cost for the standard workload",
    measurement_method="Token counts multiplied by the recorded price",
    target_operator=MetricOperator.LTE, target_value=25, unit="USD per million tokens",
)

GENERIC_CRITERION = AcceptanceCriterion(
    id=fixture_id("criterion-generic"), title="Generic Brief Understanding benchmark completed",
    description="Every active V1 candidate has results for all 100 frozen generic cases",
    verification_method="Check case-level responses and run manifest",
    evidence_requirements=["Case-level responses", "Run manifest"],
)
METRICS_CRITERION = AcceptanceCriterion(
    id=fixture_id("criterion-metrics"), title="Quality, latency, and cost results completed",
    description="Every candidate has traceable quality, P95 latency, and normalized cost results",
    verification_method="Check score sheet, latency logs, and cost calculation",
    evidence_requirements=["Quality score sheet", "Latency log", "Cost calculation"],
)
REPORT_CRITERION = AcceptanceCriterion(
    id=fixture_id("criterion-report"), title="Recommendation report approved",
    description="The report compares V1 results and explains the recommendation",
    verification_method="Review report sections and evidence links",
    evidence_requirements=["Model comparison", "Recommendation", "Evidence index"],
)

VERSION_V1 = RequirementVersion(
    id=fixture_id("version-v1"), raw_requirement_id=RAW_REQUIREMENT.id, version_number=1,
    objective="Compare candidate models for Brief Understanding and identify suitable models for the business.",
    scope=["Generic Brief Understanding test set", "Quality evaluation", "Latency comparison", "Cost comparison"],
    out_of_scope=["Project-specific validation", "Final production deployment"],
    constraints=["Use identical prompts, settings, and runtime conditions", "Use the frozen 100-case generic test set"],
    expected_outputs=["Benchmark results", "Model comparison", "Recommendation report"],
    metrics=[QUALITY_METRIC, LATENCY_METRIC, COST_METRIC],
    acceptance_criteria=[GENERIC_CRITERION, METRICS_CRITERION, REPORT_CRITERION],
    additional_fields=[
        RequirementField(
            id=fixture_id("field-candidates-v1"), key="candidate_models", label="Candidate models",
            value=["GPT-5", "Claude Sonnet", "Gemini Pro", "Doubao 1.5"],
            field_type=FieldType.LIST, required=True, source="clarification answer", confidence=1,
        ),
        RequirementField(
            id=fixture_id("field-weights-v1"), key="ranking_weights", label="Selection weights",
            value={"quality": 0.6, "latency": 0.2, "cost": 0.2},
            field_type=FieldType.OBJECT, required=True,
        ),
    ], created_by="产品负责人", change_summary="Initial clarified requirement", created_at=NOW,
)

REPORT_DELIVERABLE_ID = fixture_id("deliverable-report")
EVIDENCE_DELIVERABLE_ID = fixture_id("deliverable-evidence")
PREPARE_TASK_ID = fixture_id("task-prepare-generic")
CONFIGURE_TASK_ID = fixture_id("task-configure-models")
GENERIC_TASK_ID = fixture_id("task-run-generic")
QUALITY_TASK_ID = fixture_id("task-evaluate-quality")
METRICS_TASK_ID = fixture_id("task-collect-latency-cost")
ANALYZE_TASK_ID = fixture_id("task-compare-results")
REPORT_TASK_ID = fixture_id("task-report")

EXECUTION_PLAN = ExecutionPlan(
    id=fixture_id("plan-v1"), requirement_version_id=VERSION_V1.id,
    objective="Execute V1 reproducibly and produce a supported recommendation",
    tasks=[
        Task(id=PREPARE_TASK_ID, title="Prepare generic test set", description="Freeze 100 cases and the scoring rubric", requirement_references=["scope[0]", "constraints[1]"], deliverable_ids=[EVIDENCE_DELIVERABLE_ID], execution_order=1, estimated_effort_hours=8, status=TaskStatus.DONE),
        Task(id=CONFIGURE_TASK_ID, title="Configure candidate models", description="Apply consistent prompts, parameters, and runtime settings", dependencies=[PREPARE_TASK_ID], requirement_references=["additional_fields.candidate_models", "constraints[0]"], deliverable_ids=[EVIDENCE_DELIVERABLE_ID], execution_order=2, estimated_effort_hours=4, status=TaskStatus.DONE),
        Task(id=GENERIC_TASK_ID, title="Run generic benchmark", description="Run every candidate over all frozen cases", dependencies=[CONFIGURE_TASK_ID], acceptance_criterion_ids=[GENERIC_CRITERION.id], deliverable_ids=[EVIDENCE_DELIVERABLE_ID], execution_order=3, estimated_effort_hours=16, status=TaskStatus.DONE),
        Task(id=QUALITY_TASK_ID, title="Evaluate quality", description="Blind-score correctness, completeness, and instruction following", dependencies=[GENERIC_TASK_ID], acceptance_criterion_ids=[METRICS_CRITERION.id], deliverable_ids=[EVIDENCE_DELIVERABLE_ID], execution_order=4, estimated_effort_hours=12, status=TaskStatus.DONE),
        Task(id=METRICS_TASK_ID, title="Collect latency and cost", description="Calculate P95 latency and normalized token cost", dependencies=[GENERIC_TASK_ID], acceptance_criterion_ids=[METRICS_CRITERION.id], deliverable_ids=[EVIDENCE_DELIVERABLE_ID], execution_order=5, estimated_effort_hours=6, status=TaskStatus.DONE),
        Task(id=ANALYZE_TASK_ID, title="Compare results", description="Apply approved weights and explain trade-offs", dependencies=[QUALITY_TASK_ID, METRICS_TASK_ID], requirement_references=["metrics", "additional_fields.ranking_weights"], deliverable_ids=[REPORT_DELIVERABLE_ID], execution_order=6, estimated_effort_hours=6, status=TaskStatus.DONE),
        Task(id=REPORT_TASK_ID, title="Produce recommendation report", description="Document comparison, evidence, limitations, and recommendation", dependencies=[ANALYZE_TASK_ID], acceptance_criterion_ids=[REPORT_CRITERION.id], deliverable_ids=[REPORT_DELIVERABLE_ID], execution_order=7, estimated_effort_hours=8, status=TaskStatus.IN_PROGRESS),
    ],
    deliverables=[
        Deliverable(id=EVIDENCE_DELIVERABLE_ID, name="Benchmark evidence package", description="Cases, responses, scores, latency, cost, and run metadata", format="JSONL and CSV", task_ids=[PREPARE_TASK_ID, CONFIGURE_TASK_ID, GENERIC_TASK_ID, QUALITY_TASK_ID, METRICS_TASK_ID], acceptance_criterion_ids=[GENERIC_CRITERION.id, METRICS_CRITERION.id]),
        Deliverable(id=REPORT_DELIVERABLE_ID, name="Model comparison and recommendation", description="Trade-off analysis and supported recommendation", format="Markdown", task_ids=[ANALYZE_TASK_ID, REPORT_TASK_ID], acceptance_criterion_ids=[REPORT_CRITERION.id]),
    ], created_at=NOW,
)

PROJECT_CRITERION = AcceptanceCriterion(
    id=fixture_id("criterion-project"), title="Project-specific benchmark completed",
    description="Every active candidate has results for the approved project test set",
    verification_method="Check project results and business review",
    evidence_requirements=["Project responses", "Business review scores"],
)
SUPPLEMENTAL_CRITERION = AcceptanceCriterion(
    id=fixture_id("criterion-supplemental"), title="Additional test cases completed",
    description="Missing and boundary scenarios are added and executed",
    verification_method="Review coverage map and supplemental results",
    evidence_requirements=["Coverage map", "Supplemental case results"],
)
FINAL_VALIDATION_CRITERION = AcceptanceCriterion(
    id=fixture_id("criterion-final-validation"), title="Top 2 Final Validation completed",
    description="The two highest-ranked models pass independent final validation",
    verification_method="Check ranking, independent results, and approval",
    evidence_requirements=["Top 2 selection", "Final validation results", "Business approval"],
)
REPORT_CRITERION_V2 = REPORT_CRITERION.model_copy(update={
    "description": "The final recommendation uses generic and project-specific results and is approved"
})

VERSION_V2 = RequirementVersion(
    id=fixture_id("version-v2"), raw_requirement_id=RAW_REQUIREMENT.id, version_number=2,
    previous_version_id=VERSION_V1.id, objective=VERSION_V1.objective,
    scope=["Generic Brief Understanding test set", "Project-specific test set", "Additional missing and boundary cases", "Quality evaluation", "Latency comparison", "Cost comparison", "Top 2 Final Validation"],
    out_of_scope=["Final production deployment"],
    constraints=["Use identical prompts, settings, and runtime conditions", "Do not continue testing Doubao 1.5 because it is being retired"],
    expected_outputs=VERSION_V1.expected_outputs, metrics=VERSION_V1.metrics,
    acceptance_criteria=[GENERIC_CRITERION, METRICS_CRITERION, PROJECT_CRITERION, SUPPLEMENTAL_CRITERION, FINAL_VALIDATION_CRITERION, REPORT_CRITERION_V2],
    additional_fields=[
        RequirementField(id=fixture_id("field-candidates-v2"), key="candidate_models", label="Active candidate models", value=["GPT-5", "Claude Sonnet", "Gemini Pro"], field_type=FieldType.LIST, required=True, source="stakeholder change request", confidence=1),
        RequirementField(id=fixture_id("field-weights-v2"), key="ranking_weights", label="Selection weights", value={"quality": 0.6, "latency": 0.2, "cost": 0.2}, field_type=FieldType.OBJECT, required=True),
    ], created_by="产品负责人",
    change_summary="Remove Doubao 1.5; add project cases, coverage supplements, and Top 2 validation",
    created_at=NOW,
)

CHANGE = RequirementChange(
    id=fixture_id("change-v2"), from_version_id=VERSION_V1.id, requested_by="业务负责人",
    reason=STAKEHOLDER_CHANGE_TEXT,
    requested_changes=["Remove Doubao 1.5", "Run project-specific tests", "Add missing and boundary cases", "Validate the Top 2"],
    requested_at=NOW, resulting_version_id=VERSION_V2.id,
)

DIFF = RequirementDiff(
    id=fixture_id("diff-v1-v2"), from_version_id=VERSION_V1.id, to_version_id=VERSION_V2.id,
    entries=[
        RequirementDiffEntry(field_path="scope.project_specific_test", category=DiffCategory.ADDED, new_value="Run a project-specific test set next week", explanation="Adds evidence from the real business context"),
        RequirementDiffEntry(field_path="scope.additional_test_cases", category=DiffCategory.ADDED, new_value="Add and run missing and boundary cases", explanation="Closes gaps discovered in the generic set"),
        RequirementDiffEntry(field_path="scope.top_2_final_validation", category=DiffCategory.ADDED, new_value="Run independent Final Validation for the Top 2", explanation="Adds a final decision gate"),
        RequirementDiffEntry(field_path="additional_fields.candidate_models[Doubao 1.5]", category=DiffCategory.REMOVED, old_value="Doubao 1.5", explanation="The model is being retired; no further test effort is justified"),
        RequirementDiffEntry(field_path="acceptance_criteria.final_recommendation", category=DiffCategory.MODIFIED, old_value="Recommendation uses generic quality, latency, and cost results", new_value="Recommendation uses generic and project results, followed by Top 2 Final Validation", explanation="Project evidence and a validation gate are now required"),
        RequirementDiffEntry(field_path="metrics", category=DiffCategory.UNCHANGED, old_value=["quality", "latency", "cost"], new_value=["quality", "latency", "cost"], explanation="Quality, latency, and cost remain the comparison dimensions"),
    ],
)

PROJECT_PREP_TASK = Task(id=fixture_id("task-project-prep"), title="Prepare project-specific test set", description="Approve and de-identify real project cases", dependencies=[PREPARE_TASK_ID], acceptance_criterion_ids=[PROJECT_CRITERION.id], execution_order=6, estimated_effort_hours=10)
SUPPLEMENT_TASK = Task(id=fixture_id("task-supplement"), title="Supplement missing and boundary cases", description="Use the coverage map to add weak and edge scenarios", dependencies=[PROJECT_PREP_TASK.id], acceptance_criterion_ids=[SUPPLEMENTAL_CRITERION.id], execution_order=7, estimated_effort_hours=8)
PROJECT_TASK = Task(id=fixture_id("task-project"), title="Run project benchmark", description="Run active candidates over project and supplemental cases", dependencies=[PROJECT_PREP_TASK.id, SUPPLEMENT_TASK.id], acceptance_criterion_ids=[PROJECT_CRITERION.id, SUPPLEMENTAL_CRITERION.id], execution_order=8, estimated_effort_hours=20)
SELECT_TOP2_TASK = Task(id=fixture_id("task-select-top2"), title="Select Top 2", description="Combine generic and project evidence to select finalists", dependencies=[ANALYZE_TASK_ID], acceptance_criterion_ids=[FINAL_VALIDATION_CRITERION.id], execution_order=10, estimated_effort_hours=4)
FINAL_VALIDATION_TASK = Task(id=fixture_id("task-final-validation"), title="Run Top 2 Final Validation", description="Run an independent set and record business approval", dependencies=[SELECT_TOP2_TASK.id], acceptance_criterion_ids=[FINAL_VALIDATION_CRITERION.id], execution_order=11, estimated_effort_hours=12)

IMPACT_ANALYSIS = ImpactAnalysis(
    id=fixture_id("impact-v2"), requirement_diff_id=DIFF.id,
    valid_task_ids=[PREPARE_TASK_ID, GENERIC_TASK_ID, QUALITY_TASK_ID, METRICS_TASK_ID],
    tasks_needing_modification=[
        TaskImpact(task_id=CONFIGURE_TASK_ID, reason="The active candidate list no longer includes Doubao 1.5", affected_requirement_paths=["additional_fields.candidate_models"], recommended_action="Disable Doubao and retain other configurations"),
        TaskImpact(task_id=ANALYZE_TASK_ID, reason="Ranking must combine generic and project evidence", affected_requirement_paths=["acceptance_criteria.final_recommendation"], recommended_action="Extend comparison after project results exist"),
        TaskImpact(task_id=REPORT_TASK_ID, reason="The report must include project evidence and Final Validation", affected_requirement_paths=["acceptance_criteria.final_recommendation"], recommended_action="Keep the draft and add new evidence before approval"),
    ], tasks_requiring_rework=[],
    new_tasks_required=[PROJECT_PREP_TASK, SUPPLEMENT_TASK, PROJECT_TASK, SELECT_TOP2_TASK, FINAL_VALIDATION_TASK],
    affected_deliverable_ids=[EVIDENCE_DELIVERABLE_ID, REPORT_DELIVERABLE_ID],
    affected_criterion_ids=[PROJECT_CRITERION.id, SUPPLEMENTAL_CRITERION.id, FINAL_VALIDATION_CRITERION.id, REPORT_CRITERION.id],
    summary="Keep generic evidence and scoring; update candidate configuration, ranking, and report; add project, coverage, Top 2, and validation work. No completed output is wholly untrustworthy.",
    analyzed_at=NOW,
)

CONFIGURE_TASK_V2 = Task(
    id=CONFIGURE_TASK_ID,
    title="Configure active candidate models",
    description="Remove Doubao 1.5 and retain consistent settings for the three active candidates",
    dependencies=[PREPARE_TASK_ID],
    requirement_references=["additional_fields.candidate_models", "constraints[0]"],
    deliverable_ids=[EVIDENCE_DELIVERABLE_ID],
    execution_order=2,
    estimated_effort_hours=2,
    status=TaskStatus.IN_PROGRESS,
)
ANALYZE_TASK_V2 = Task(
    id=ANALYZE_TASK_ID,
    title="Compare generic and project results",
    description="Combine all quality, latency, and cost evidence and apply approved weights",
    dependencies=[QUALITY_TASK_ID, METRICS_TASK_ID, PROJECT_TASK.id],
    requirement_references=["metrics", "additional_fields.ranking_weights"],
    deliverable_ids=[REPORT_DELIVERABLE_ID],
    execution_order=9,
    estimated_effort_hours=8,
)
REPORT_TASK_V2 = Task(
    id=REPORT_TASK_ID,
    title="Finalize recommendation report",
    description="Document generic and project evidence, Top 2 validation, and final recommendation",
    dependencies=[FINAL_VALIDATION_TASK.id],
    acceptance_criterion_ids=[REPORT_CRITERION.id],
    deliverable_ids=[REPORT_DELIVERABLE_ID],
    execution_order=12,
    estimated_effort_hours=8,
)

EXECUTION_PLAN_V2 = revise_execution_plan(
    EXECUTION_PLAN,
    VERSION_V2,
    DIFF,
    IMPACT_ANALYSIS,
    id=fixture_id("plan-v2"),
    objective="Complete the expanded V2 benchmark and validate the Top 2 before recommendation",
    modified_tasks=[CONFIGURE_TASK_V2, ANALYZE_TASK_V2, REPORT_TASK_V2],
    deliverables=[
        Deliverable(
            id=EVIDENCE_DELIVERABLE_ID,
            name="Expanded benchmark evidence package",
            description="Generic, project, supplemental, quality, latency, cost, and validation evidence",
            format="JSONL and CSV",
            task_ids=[PREPARE_TASK_ID, CONFIGURE_TASK_ID, GENERIC_TASK_ID, QUALITY_TASK_ID, METRICS_TASK_ID, PROJECT_PREP_TASK.id, SUPPLEMENT_TASK.id, PROJECT_TASK.id, FINAL_VALIDATION_TASK.id],
            acceptance_criterion_ids=[GENERIC_CRITERION.id, METRICS_CRITERION.id, PROJECT_CRITERION.id, SUPPLEMENTAL_CRITERION.id, FINAL_VALIDATION_CRITERION.id],
        ),
        Deliverable(
            id=REPORT_DELIVERABLE_ID,
            name="Final model comparison and recommendation",
            description="Combined comparison, Top 2 evidence, and approved recommendation",
            format="Markdown",
            task_ids=[ANALYZE_TASK_ID, SELECT_TOP2_TASK.id, REPORT_TASK_ID],
            acceptance_criterion_ids=[REPORT_CRITERION.id],
        ),
    ],
    created_at=NOW,
)

COMPLETION_EVALUATION = evaluate_completion(
    VERSION_V2,
    EXECUTION_PLAN_V2,
    id=fixture_id("completion-v2"),
    criterion_results=[
        CriterionEvaluation(criterion_id=GENERIC_CRITERION.id, status=CriterionStatus.PASS, evidence=["evidence/generic-responses.jsonl", "evidence/run-manifest.json"], explanation="Generic benchmark is complete and remains valid"),
        CriterionEvaluation(criterion_id=METRICS_CRITERION.id, status=CriterionStatus.PASS, evidence=["evidence/quality.csv", "evidence/latency.csv", "evidence/cost.csv"], explanation="Quality, latency, and cost results are complete"),
        CriterionEvaluation(criterion_id=PROJECT_CRITERION.id, status=CriterionStatus.MISSING_EVIDENCE, evidence=[], explanation="The project-specific benchmark has not been run"),
        CriterionEvaluation(criterion_id=SUPPLEMENTAL_CRITERION.id, status=CriterionStatus.MISSING_EVIDENCE, evidence=[], explanation="Missing and boundary cases have not been added or run"),
        CriterionEvaluation(criterion_id=FINAL_VALIDATION_CRITERION.id, status=CriterionStatus.MISSING_EVIDENCE, evidence=[], explanation="Top 2 selection, validation results, and approval are absent"),
        CriterionEvaluation(criterion_id=REPORT_CRITERION.id, status=CriterionStatus.NOT_YET_COMPLETE, evidence=["draft/model-comparison.md"], explanation="The draft cannot be finalized before project testing and Final Validation"),
    ],
    overall_status=CompletionStatus.PARTIALLY_COMPLETED,
    unresolved_items=["Run the project-specific benchmark", "Add and execute missing and boundary cases", "Select and validate the Top 2", "Finalize and approve the recommendation report"],
    evaluated_at=NOW,
)
