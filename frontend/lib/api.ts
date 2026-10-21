import type {
  AnalyzeResponse,
  ConsultingApproach,
  ConsultingProposalDocument,
  ChangeBundle,
  ClarificationQuestion,
  CompletionEvaluation,
  ExecutionPlan,
  Proposal,
  RawRequirement,
  RequirementAnalysis,
  RequirementVersion,
} from "./types";

// The browser calls public same-origin paths routed by root vercel.json.
// Development still uses the local FastAPI server on port 8100.
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ??
  (process.env.NODE_ENV === "production" ? "" : "http://localhost:8100");

async function request<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "请求失败" }));
    throw new Error(error.detail ?? `请求失败 (${response.status})`);
  }
  return response.json();
}

export const analyzeRequirement = (text: string) =>
  request<AnalyzeResponse>("/requirements/analyze", {
    request: text,
    title: "Client Brief",
    submitted_by: "Consultant",
    source: "Client brief",
  });

export const alignRequirement = (
  raw: RawRequirement,
  analysis: RequirementAnalysis,
  questions: ClarificationQuestion[],
) =>
  request<{ mode: string; proposal: Proposal<RequirementVersion> }>("/requirements/align", {
    raw_requirement: raw,
    analysis,
    answered_clarification_questions: questions,
  });

export const generatePlan = (requirement: Proposal<RequirementVersion>) =>
  request<{ mode: string; proposal: Proposal<ExecutionPlan> }>("/plans/generate", { requirement });

export const analyzeChange = (
  raw: RawRequirement,
  requirement: Proposal<RequirementVersion>,
  plan: Proposal<ExecutionPlan>,
  message: string,
) =>
  request<{ mode: string; proposal: Proposal<ChangeBundle> }>("/changes/analyze", {
    raw_requirement: raw,
    current_requirement: requirement,
    current_plan: plan,
    stakeholder_change: message,
  });

export const evaluateCompletion = (
  requirement: Proposal<RequirementVersion>,
  plan: Proposal<ExecutionPlan>,
) =>
  request<{ mode: string; proposal: Proposal<CompletionEvaluation> }>("/completion/evaluate", {
    current_requirement: requirement,
    current_plan: plan,
    evidence_status: [],
  });

export function confirm<T>(proposal: Proposal<T>): Proposal<T> {
  return { ...proposal, confirmation_status: "USER_CONFIRMED" };
}

const key = "requirement-alignment-session";

export type WorkspaceState = {
  analysis?: AnalyzeResponse;
  requirementV1?: Proposal<RequirementVersion>;
  planV1?: Proposal<ExecutionPlan>;
  change?: Proposal<ChangeBundle>;
  completion?: Proposal<CompletionEvaluation>;
  approach?: Proposal<ConsultingApproach>;
  consultingProposal?: ConsultingProposalDocument;
};

export function loadWorkspace(): WorkspaceState {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(sessionStorage.getItem(key) ?? "{}");
  } catch {
    return {};
  }
}

export function clearWorkspace(): void {
  if (typeof window !== "undefined") sessionStorage.removeItem(key);
}

export function saveWorkspace(patch: Partial<WorkspaceState>): WorkspaceState {
  const next = { ...loadWorkspace(), ...patch };
  sessionStorage.setItem(key, JSON.stringify(next));
  return next;
}

export const SAMPLE_REQUEST = "测试不同模型的能力评分，看看哪个模型比较适合我们的业务。";
export const CHANGE_REQUEST = "豆包 1.5 快下架了，不需要继续测试。\n下周跑项目测试集并继续补充测试集，\n最后对 Top 2 做 Final Validation。";

export async function bootstrapV1(): Promise<WorkspaceState> {
  const existing = loadWorkspace();
  if (existing.analysis && existing.requirementV1 && existing.planV1) return existing;
  const analysis = existing.analysis ?? await analyzeRequirement(SAMPLE_REQUEST);
  const aligned = await alignRequirement(
    analysis.raw_requirement.payload,
    analysis.analysis.payload,
    analysis.clarification_questions.payload,
  );
  const requirementV1 = confirm(aligned.proposal);
  const planned = await generatePlan(requirementV1);
  const planV1 = confirm(planned.proposal);
  return saveWorkspace({ analysis, requirementV1, planV1 });
}

export const generateConsultingApproach = (requirement:Proposal<RequirementVersion>) =>
  request<{mode:string;proposal:Proposal<ConsultingApproach>}>("/consulting/approach",{requirement});
export const generateConsultingProposal = (project_id:string,requirement:Proposal<RequirementVersion>,approach:ConsultingApproach) =>
  request<ConsultingProposalDocument>("/consulting/proposal",{project_id,requirement,approach});
export async function previewConsultingProposal(proposal:ConsultingProposalDocument):Promise<string>{
  const response=await fetch(`${API_BASE}/consulting/proposal/preview`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({proposal})});
  if(!response.ok)throw new Error(`HTML Preview failed (${response.status})`);
  return response.text();
}
