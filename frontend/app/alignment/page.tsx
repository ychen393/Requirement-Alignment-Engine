"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { ClarificationQuestion } from "@/components/ClarificationQuestion";
import { ProgressSteps } from "@/components/ProgressSteps";
import { RequirementDocument } from "@/components/RequirementDocument";
import {
  alignRequirement,
  analyzeRequirement,
  confirm,
  loadWorkspace,
  saveWorkspace,
} from "@/lib/api";
import type { AnalyzeResponse, ClarificationQuestion as Question, Proposal, RequirementVersion } from "@/lib/types";
import { zh } from "@/lib/copy";

export default function AlignmentPage() {
  const router = useRouter();
  const [analysis, setAnalysis] = useState<AnalyzeResponse>();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [draftLoading, setDraftLoading] = useState(false);
  const [proposal, setProposal] = useState<Proposal<RequirementVersion>>();
  const [requirement, setRequirement] = useState<RequirementVersion>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function prepare() {
      try {
        const stored = loadWorkspace();
        const base = stored.analysis;
        if (!base) { router.replace("/new"); return; }
        setAnalysis(base);
        const qs = base.clarification_questions.payload.map((item) => ({
          ...item,
          question: zh(item.question),
          answer: item.answer ? zh(item.answer) : item.answer,
        }));
        setQuestions(qs);
        // Only restore a previously confirmed draft. New drafts must be based on
        // answered clarification questions, not the original unanswered list.
        if (stored.requirementV1?.confirmation_status === "USER_CONFIRMED") {
          setProposal(stored.requirementV1);
          setRequirement(stored.requirementV1.payload);
        }
      } catch (caught) { setError(caught instanceof Error ? caught.message : "加载失败"); }
      finally { setLoading(false); }
    }
    prepare();
  }, []);

  const answered = useMemo(() => questions.filter((q) => q.answer?.trim()).length, [questions]);

  function updateAnswer(id: string, answer: string) {
    // Editing any answer invalidates the previously generated requirement draft.
    setProposal(undefined);
    setRequirement(undefined);
    setQuestions((current) => current.map((q) => q.id === id ? {
      ...q,
      answer,
      status: answer.trim() ? "ANSWERED" : "OPEN",
      answered_by: answer.trim() ? "Yihan" : null,
      answered_at: answer.trim() ? new Date().toISOString() : null,
    } : q));
  }

  async function prepareRequirementDraft() {
    if (!analysis || answered !== questions.length) {
      setError("请先回答全部澄清问题。"); return;
    }
    setDraftLoading(true); setError("");
    try {
      const aligned = await alignRequirement(
        analysis.raw_requirement.payload,
        analysis.analysis.payload,
        questions,
      );
      const source = aligned.proposal.payload;
      const localized = {
        ...source,
        objective: zh(source.objective),
        scope: source.scope.map(zh),
        out_of_scope: source.out_of_scope.map(zh),
        constraints: source.constraints.map(zh),
        expected_outputs: source.expected_outputs.map(zh),
        acceptance_criteria: source.acceptance_criteria.map((item) => ({
          ...item, title: zh(item.title),
        })),
      };
      setProposal(aligned.proposal);
      setRequirement(localized);
      // A draft is intentionally not stored as a confirmed requirement.
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "生成草案失败");
    } finally { setDraftLoading(false); }
  }

  async function confirmRequirement() {
    if (!proposal || !requirement || answered !== questions.length) {
      setError("请先回答全部关键问题，再确认 Requirement V1。"); return;
    }
    setLoading(true); setError("");
    try {
      const confirmedRequirement = confirm({ ...proposal, payload: requirement });
      saveWorkspace({ requirementV1: confirmedRequirement, approach: undefined, consultingProposal: undefined });
      router.push("/approach");
    } catch (caught) { setError(caught instanceof Error ? caught.message : "确认失败"); }
    finally { setLoading(false); }
  }

  if (loading && !analysis) return <main className="loading-page">正在整理需求文档…</main>;
  if (!analysis) return <main className="loading-page error-message">{error || "无法加载需求"}</main>;

  return (
    <main className="page-shell alignment-page">
      <div className="page-top"><Breadcrumbs items={["Client Brief", "Requirement V1"]} /><ProgressSteps current={3} /></div>
      <div className="alignment-title"><div><h1>需求对齐 <span className="status-pill orange">待确认</span></h1><p>完善需求核心内容，回答澄清问题，确认后进入咨询方法论与 Workstreams 设计。</p></div></div>
      <div className="alignment-grid">
        <aside className="source-column">
          <h2>原始需求</h2>
          <blockquote>{analysis.raw_requirement.payload.description}</blockquote>
          <dl><div><dt>来源</dt><dd>Client Brief</dd></div><div><dt>提交时间</dt><dd>当前会话</dd></div><div><dt>需求 ID</dt><dd>{analysis.raw_requirement.payload.id.slice(0, 8)}</dd></div></dl>
          <div className="landscape" aria-hidden="true"><i/><i/><i/></div>
        </aside>
        {requirement ? <RequirementDocument requirement={requirement} onChange={setRequirement} /> : <section className="paper-panel"><h2>先完成需求澄清</h2><p>回答右侧问题后，再根据你的真实答案生成可编辑的需求草案。</p><button className="button primary" disabled={draftLoading || answered !== questions.length} onClick={prepareRequirementDraft}>{draftLoading ? "正在生成草案…" : "基于澄清答案生成需求草案 →"}</button></section>}
        <aside className="questions-column">
          <div className="questions-heading"><h2>待确认问题</h2><b>{answered} / {questions.length}</b></div>
          <div className="question-list">{questions.map((question, index) => <ClarificationQuestion key={question.id} question={question} index={index} onAnswer={(answer) => updateAnswer(question.id, answer)} />)}</div>
        </aside>
      </div>
      <div className="sticky-confirm"><div><b>确认后将进入 Consulting Approach。</b><span>后续需求变化不会覆盖当前版本，而会创建新的版本。</span></div><button className="button primary" onClick={confirmRequirement} disabled={loading || !requirement || !proposal || answered !== questions.length}>{loading ? "正在确认…" : "确认 Requirement V1 →"}</button></div>
      {error && <p className="error-message floating-error">{error}</p>}
    </main>
  );
}
