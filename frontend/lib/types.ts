export type ConfirmationStatus = "AI_SUGGESTED" | "USER_CONFIRMED";

export interface Proposal<T> {
  confirmation_status: ConfirmationStatus;
  payload: T;
}

export interface AnalysisItem {
  id: string;
  description: string;
  evidence?: string | null;
  affected_fields: string[];
}

export interface RiskItem extends AnalysisItem {
  likelihood: string;
  impact: string;
  mitigation?: string | null;
}

export interface RawRequirement {
  id: string;
  title: string;
  description: string;
  submitted_by: string;
  source: string;
  status: string;
  created_at: string;
}

export interface RequirementAnalysis {
  id: string;
  raw_requirement_id: string;
  confirmed_information: AnalysisItem[];
  missing_information: AnalysisItem[];
  assumptions: AnalysisItem[];
  ambiguities: AnalysisItem[];
  risks: RiskItem[];
  analyzed_at: string;
}

export interface ClarificationQuestion {
  id: string;
  analysis_id: string;
  question: string;
  rationale: string;
  target_field: string;
  priority: string;
  status: "OPEN" | "ANSWERED" | "DISMISSED";
  answer?: string | null;
  answered_by?: string | null;
  answered_at?: string | null;
}

export interface Metric {
  id: string;
  name: string;
  description: string;
  measurement_method: string;
  target_operator: string;
  target_value: number | string | number[];
  unit?: string | null;
}

export interface AcceptanceCriterion {
  id: string;
  title: string;
  description: string;
  verification_method: string;
  metric_id?: string | null;
  required: boolean;
  evidence_requirements: string[];
}

export interface RequirementVersion {
  id: string;
  raw_requirement_id: string;
  version_number: number;
  previous_version_id?: string | null;
  objective: string;
  scope: string[];
  out_of_scope: string[];
  constraints: string[];
  expected_outputs: string[];
  metrics: Metric[];
  acceptance_criteria: AcceptanceCriterion[];
  additional_fields: Array<{ id: string; key: string; label: string; value: unknown }>;
  created_by: string;
  change_summary?: string | null;
  is_current: boolean;
  created_at: string;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: "NOT_STARTED" | "IN_PROGRESS" | "BLOCKED" | "DONE" | "INVALIDATED";
  dependencies: string[];
  requirement_references: string[];
  acceptance_criterion_ids: string[];
  deliverable_ids: string[];
  estimated_effort_hours?: number | null;
  execution_order: number;
}

export interface ExecutionPlan {
  id: string;
  requirement_version_id: string;
  objective: string;
  tasks: Task[];
  deliverables: unknown[];
  created_at: string;
}

export interface RequirementDiffEntry {
  id: string;
  field_path: string;
  category: "ADDED" | "REMOVED" | "MODIFIED" | "UNCHANGED";
  old_value: unknown;
  new_value: unknown;
  explanation: string;
}

export interface ImpactAnalysis {
  id: string;
  requirement_diff_id: string;
  valid_task_ids: string[];
  tasks_needing_modification: Array<{ task_id: string; reason: string; recommended_action: string }>;
  tasks_requiring_rework: Array<{ task_id: string; reason: string; recommended_action: string }>;
  new_tasks_required: Task[];
  summary: string;
}

export interface ChangeBundle {
  requirement_version: RequirementVersion;
  requirement_diff: { id: string; from_version_id: string; to_version_id: string; entries: RequirementDiffEntry[] };
  impact_analysis: ImpactAnalysis;
  revised_execution_plan: ExecutionPlan;
}

export interface CriterionEvaluation {
  id: string;
  criterion_id: string;
  status: "PASS" | "FAIL" | "MISSING_EVIDENCE" | "NOT_YET_COMPLETE";
  evidence: string[];
  observed_value: unknown;
  explanation: string;
}

export interface CompletionEvaluation {
  id: string;
  requirement_version_id: string;
  execution_plan_id: string;
  criterion_results: CriterionEvaluation[];
  completed_criteria: string[];
  failed_criteria: string[];
  missing_evidence: string[];
  overall_status: string;
  unresolved_items: string[];
  evaluated_at: string;
}

export interface AnalyzeResponse {
  mode: "AI" | "DEMO";
  raw_requirement: Proposal<RawRequirement>;
  analysis: Proposal<RequirementAnalysis>;
  clarification_questions: Proposal<ClarificationQuestion[]>;
}
