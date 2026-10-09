"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AIComment } from "@/components/AIComment";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { ConfirmationStatus } from "@/components/ConfirmationStatus";
import { ExecutionTask } from "@/components/ExecutionTask";
import { RequirementDiff } from "@/components/RequirementDiff";
import {
  analyzeChange,
  bootstrapV1,
  CHANGE_REQUEST,
  confirm,
  loadWorkspace,
  saveWorkspace,
} from "@/lib/api";
import type { ChangeBundle, ExecutionPlan, Proposal } from "@/lib/types";
import { zh } from "@/lib/copy";

export default function ExecutionPage() {
  const router = useRouter();
  const [plan, setPlan] = useState<ExecutionPlan>();
  const [baselinePlan, setBaselinePlan] = useState<ExecutionPlan>();
  const [change, setChange] = useState<Proposal<ChangeBundle>>();
  const [showComposer, setShowComposer] = useState(false);
  const [message, setMessage] = useState(CHANGE_REQUEST);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function prepare() {
      try {
        const state = await bootstrapV1();
        const savedChange = state.change;
        setChange(savedChange);
        setBaselinePlan(state.planV1?.payload);
        setPlan(savedChange?.payload.revised_execution_plan ?? state.planV1?.payload);
      } catch (caught) { setError(caught instanceof Error ? caught.message : "加载失败"); }
      finally { setLoading(false); }
    }
    prepare();
  }, []);

  async function reviewChange() {
    setLoading(true); setError("");
    try {
      const state = loadWorkspace();
      if (!state.analysis || !state.requirementV1 || !state.planV1) throw new Error("缺少 V1 工作区数据");
      const response = await analyzeChange(
        state.analysis.raw_requirement.payload,
        confirm(state.requirementV1),
        confirm(state.planV1),
        message,
      );
      setChange(response.proposal); setPlan(response.proposal.payload.revised_execution_plan);
      saveWorkspace({ change: response.proposal }); setShowComposer(false);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "变更分析失败"); }
    finally { setLoading(false); }
  }

  function confirmChange() {
    if (!change) return;
    const confirmed = confirm(change);
    saveWorkspace({ change: confirmed }); setChange(confirmed);
    router.push("/review");
  }

  const completed = useMemo(() => plan?.tasks.filter((task) => task.status === "DONE").length ?? 0, [plan]);
  const baselineCompleted = useMemo(() => baselinePlan?.tasks.filter((task) => task.status === "DONE").length ?? 0, [baselinePlan]);
  const keptTasks = useMemo(() => {
    if (!change || !baselinePlan) return [];
    const ids = new Set(change.payload.impact_analysis.valid_task_ids);
    return baselinePlan.tasks.filter((task) => ids.has(task.id)).map((task) => zh(task.title));
  }, [change, baselinePlan]);

  function taskChangeTag(taskId: string) {
    if (!change) return undefined;
    const impact = change.payload.impact_analysis;
    if (impact.valid_task_ids.includes(taskId)) return { label: "已有任务", tone: "existing" as const };
    if (impact.tasks_needing_modification.some((item) => item.task_id === taskId)) return { label: "因 V2 调整", tone: "modified" as const };
    if (impact.tasks_requiring_rework.some((item) => item.task_id === taskId)) return { label: "需要返工", tone: "rework" as const };
    if (impact.new_tasks_required.some((task) => task.id === taskId)) return { label: "V2 新增", tone: "new" as const };
    return undefined;
  }
  if (loading && !plan) return <main className="loading-page">正在加载执行计划…</main>;
  if (!plan) return <main className="loading-page error-message">{error || "无法加载执行计划"}</main>;

  return (
    <main className="page-shell execution-page">
      <div className="page-top"><Breadcrumbs items={["模型能力 Benchmark", `Requirement ${change ? "V2" : "V1"}`]} /></div>
      <header className="execution-header">
        <div><span className="eyebrow">执行计划</span><h1>执行计划 <span className="status-pill green">执行中</span></h1><p>当前版本 <b>{change ? "V2" : "V1"}</b>　·　{completed} / {plan.tasks.length} 已完成</p></div>
        <button className="button secondary" onClick={() => setShowComposer(!showComposer)}>＋ 记录需求变更</button>
      </header>

      {showComposer && <section className="change-composer paper-panel"><div><span className="eyebrow">利益相关方变更</span><h2>记录需求变更</h2><p>粘贴新的需求或决策。AI 会保留仍然有效的工作，并说明需要调整和新增的内容。</p></div><textarea value={message} onChange={(e) => setMessage(e.target.value)} /><button className="button primary" onClick={reviewChange} disabled={loading}>{loading ? "正在分析…" : "分析需求变更 →"}</button></section>}

      {change && <section className="change-story paper-panel" aria-label="Requirement V1 到 V2 的变更过程">
        <div className="story-stage before"><span>变更前</span><b>Requirement V1</b><strong>{baselineCompleted} / {baselinePlan?.tasks.length ?? 7}</strong><small>任务已完成，执行已在进行</small></div>
        <span className="story-arrow">→</span>
        <div className="story-event"><span>利益相关方提出变更</span><blockquote>{message}</blockquote></div>
        <span className="story-arrow">→</span>
        <div className="story-stage after"><span>变更后</span><b>Requirement V2</b><strong>{plan.tasks.length}</strong><small>个任务，等待你确认</small></div>
        <p>需求发生变化，但已完成且仍有效的工作不会被推翻。</p>
      </section>}

      <div className="execution-layout">
        <section className="task-timeline paper-panel">
          <div className="tabs"><button className="active">当前计划（{change ? "V2" : "V1"}）</button><button>历史版本</button><button>变更记录</button></div>
          <div>{plan.tasks.map((task) => <ExecutionTask task={task} changeTag={taskChangeTag(task.id)} key={task.id} />)}</div>
        </section>

        <aside className="impact-sidebar">
          {!change && <AIComment title="执行中的计划"><p>已完成工作会在需求变更时被优先保留。点击“记录需求变更”体验选择性影响分析。</p></AIComment>}
          {change && <>
            <div className="impact-title"><div><h2>需求变更分析</h2><p>Requirement V1 → V2</p></div><ConfirmationStatus status={change.confirmation_status} /></div>
            <section className="preservation-summary">
              <span className="eyebrow">影响结论</span><h2>哪些工作还能保留？</h2>
              <div className="impact-counts"><div><b>{change.payload.impact_analysis.valid_task_ids.length}</b><span>保留</span></div><div><b>{change.payload.impact_analysis.tasks_needing_modification.length}</b><span>调整</span></div><div><b>{change.payload.impact_analysis.new_tasks_required.length}</b><span>新增</span></div><div><b>{change.payload.impact_analysis.tasks_requiring_rework.length}</b><span>返工</span></div></div>
            </section>
            <AIComment title="AI 影响判断"><p>{zh(change.payload.impact_analysis.summary)}</p></AIComment>
            <div className="impact-groups">
              <ImpactGroup tone="keep" title="保留已有工作" count={change.payload.impact_analysis.valid_task_ids.length} items={keptTasks} />
              <ImpactGroup tone="modify" title="需要调整" count={change.payload.impact_analysis.tasks_needing_modification.length} items={change.payload.impact_analysis.tasks_needing_modification.map((item) => zh(item.recommended_action))} />
              <ImpactGroup tone="add" title="新增任务" count={change.payload.impact_analysis.new_tasks_required.length} items={change.payload.impact_analysis.new_tasks_required.map((task) => zh(task.title))} />
              <p className="no-rework">✓ 无需返工　已有有效工作不会被推翻。</p>
            </div>
          </>}
        </aside>
      </div>

      {change && <section className="diff-review paper-panel">
        <div className="diff-header"><div><span className="eyebrow">版本对比</span><h2>Requirement V1 → V2</h2></div><p>以文档修订方式查看这次变化</p></div>
        <RequirementDiff entries={change.payload.requirement_diff.entries} />
        <div className="plan-shift"><div><b>Requirement V1</b><span>{baselineCompleted} / {baselinePlan?.tasks.length ?? 7} 已完成</span></div><strong>→</strong><div><b>Requirement V2</b><span>{plan.tasks.length} 个任务 · 新增 {change.payload.impact_analysis.new_tasks_required.length}</span></div></div>
        <div className="diff-actions"><button className="button secondary" onClick={() => setShowComposer(true)}>编辑变更内容</button><button className="button primary" onClick={confirmChange}>{change.confirmation_status === "USER_CONFIRMED" ? "变更已确认 →" : "确认变更并更新执行计划 →"}</button></div>
      </section>}
      {error && <p className="error-message floating-error">{error}</p>}
    </main>
  );
}

function ImpactGroup({ tone, title, count, items }: { tone: string; title: string; count: number; items: string[] }) {
  return <section className={`impact-group ${tone}`}><h3><span>{tone === "keep" ? "✓" : tone === "modify" ? "△" : "+"}</span>{title}<b>{count}</b></h3><ul>{items.map((item) => <li key={item}>{item}</li>)}</ul></section>;
}
