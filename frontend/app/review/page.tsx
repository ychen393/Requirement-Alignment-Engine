"use client";

import { useEffect, useMemo, useState } from "react";
import { AIComment } from "@/components/AIComment";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { ConfirmationStatus } from "@/components/ConfirmationStatus";
import { EvidenceRow } from "@/components/EvidenceRow";
import { confirm, evaluateCompletion, loadWorkspace, saveWorkspace } from "@/lib/api";
import type { CompletionEvaluation, Proposal, RequirementVersion } from "@/lib/types";

export default function ReviewPage() {
  const [evaluation, setEvaluation] = useState<Proposal<CompletionEvaluation>>();
  const [requirement, setRequirement] = useState<RequirementVersion>();
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function prepare() {
      try {
        const state = loadWorkspace();
        if (!state.change) throw new Error("请先确认 Requirement V2 与修订计划");
        const requirementProposal = confirm({ confirmation_status: "AI_SUGGESTED", payload: state.change.payload.requirement_version } as const);
        const planProposal = confirm({ confirmation_status: "AI_SUGGESTED", payload: state.change.payload.revised_execution_plan } as const);
        setRequirement(requirementProposal.payload);
        const response = state.completion ? { proposal: state.completion } : await evaluateCompletion(requirementProposal, planProposal);
        setEvaluation(response.proposal); saveWorkspace({ completion: response.proposal });
      } catch (caught) { setError(caught instanceof Error ? caught.message : "验收加载失败"); }
    }
    prepare();
  }, []);

  const passed = useMemo(() => evaluation?.payload.criterion_results.filter((item) => item.status === "PASS").length ?? 0, [evaluation]);
  if (!evaluation || !requirement) return <main className="loading-page">{error || "正在整理验收证据…"}</main>;

  const byCriterion = new Map(evaluation.payload.criterion_results.map((item) => [item.criterion_id, item]));
  return (
    <main className="page-shell review-page">
      <div className="page-top"><Breadcrumbs items={["模型能力 Benchmark", "任务验收"]} /></div>
      <header className="review-header"><div><span className="eyebrow">验收审阅</span><h1>任务验收 <span className="version-badge">V2</span></h1><p>模型能力 Benchmark　·　依据已确认的验收标准检查执行证据</p></div><ConfirmationStatus status={confirmed ? "USER_CONFIRMED" : evaluation.confirmation_status} /></header>
      <section className="completion-summary paper-panel">
        <div className="completion-ring"><span>{Math.round(passed / requirement.acceptance_criteria.length * 100)}%</span></div>
        <div><span className="eyebrow">总体状态</span><h2>部分完成</h2><p><b>{passed} / {requirement.acceptance_criteria.length}</b> 验收标准已满足</p></div>
        <div className="summary-note">仍有关键项目证据缺失，暂时不能判定整个任务已经完成。</div>
      </section>

      <div className="review-layout">
        <section className="evidence-document paper-panel">
          <div className="tabs"><button className="active">验收标准（{requirement.acceptance_criteria.length}）</button><button>执行证据</button><button>AI 评估</button></div>
          <div className="evidence-group"><h2>已通过 <span>{passed}</span></h2>{requirement.acceptance_criteria.filter((item) => byCriterion.get(item.id)?.status === "PASS").map((item) => <EvidenceRow key={item.id} criterion={item} result={byCriterion.get(item.id)} />)}</div>
          <div className="evidence-group pending-group"><h2>待完成 <span>{requirement.acceptance_criteria.length - passed}</span></h2>{requirement.acceptance_criteria.filter((item) => byCriterion.get(item.id)?.status !== "PASS").map((item) => <EvidenceRow key={item.id} criterion={item} result={byCriterion.get(item.id)} />)}</div>
        </section>
        <aside>
          <AIComment title="AI 判断"><p>当前已有证据可以证明通用 Benchmark 和质量、延迟、成本评估已经完成。</p><p>但仍缺少项目场景验证、补充测试集和 Final Validation，因此当前不能判定整个任务已经完成。</p></AIComment>
          <div className="decision-note"><b>最终决定由你确认</b><p>AI 评估不会自动改变项目完成状态。</p></div>
        </aside>
      </div>
      <div className="review-confirm"><p>{confirmed ? "验收结果已由用户确认。项目仍保持“部分完成”状态。" : "请确认 AI 建议与证据记录是否准确。"}</p><button className="button primary" onClick={() => { const next = confirm(evaluation); setEvaluation(next); saveWorkspace({ completion: next }); setConfirmed(true); }}>{confirmed ? "✓ 已确认验收结果" : "确认验收结果 →"}</button></div>
    </main>
  );
}
