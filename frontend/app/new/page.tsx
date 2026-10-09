"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AIComment } from "@/components/AIComment";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { ConfirmationStatus } from "@/components/ConfirmationStatus";
import { ProgressSteps } from "@/components/ProgressSteps";
import { analyzeRequirement, SAMPLE_REQUEST, saveWorkspace } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";
import { zh } from "@/lib/copy";

export default function NewRequirementPage() {
  const router = useRouter();
  const [text, setText] = useState(SAMPLE_REQUEST);
  const [result, setResult] = useState<AnalyzeResponse>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyze() {
    setLoading(true); setError("");
    try {
      const data = await analyzeRequirement(text);
      setResult(data); saveWorkspace({ analysis: data });
    } catch (caught) { setError(caught instanceof Error ? caught.message : "分析失败"); }
    finally { setLoading(false); }
  }

  const findingCount = result ? {
    confirmed: result.analysis.payload.confirmed_information.length,
    missing: result.analysis.payload.missing_information.length,
    ambiguous: result.analysis.payload.ambiguities.length,
    risks: result.analysis.payload.risks.length,
  } : undefined;

  return (
    <main className="page-shell compact-page">
      <div className="page-top"><Breadcrumbs items={["新建需求"]} /><ProgressSteps current={result ? 2 : 1} /></div>
      <section className="new-header"><span className="eyebrow">需求分析</span><h1>新建需求</h1><p>粘贴领导、客户或项目方的原始需求，AI 将帮你分析关键信息并提出需要确认的问题。</p></section>
      <section className="request-entry-grid">
        <div className="request-composer">
          <label htmlFor="requirement">原始需求</label>
          <textarea id="requirement" maxLength={2000} value={text} onChange={(e) => setText(e.target.value)} placeholder="粘贴领导、客户或项目方的原始需求…" />
          <span className="character-count">{text.length} / 2000</span>
          <button className="button primary centered" onClick={analyze} disabled={loading || !text.trim()}>{loading ? "正在分析…" : result ? "重新分析需求 →" : "开始分析需求 →"}</button>
          {error && <p className="error-message">{error}</p>}
        </div>
        {!findingCount ? <AIComment title="AI 会帮你分析"><ul><li>已确认的信息</li><li>需要进一步确认的内容</li><li>可能的模糊点和风险</li><li>并提出有价值的澄清问题</li></ul></AIComment> :
          <aside className="analysis-summary">
            <span className="analysis-complete">✓ 分析完成</span>
            <h2>这句需求还不能直接开始执行</h2>
            <p>AI 已找出需要你确认的关键信息。</p>
            <dl><div><dt>{findingCount.confirmed}</dt><dd>已确认</dd></div><div><dt>{findingCount.missing}</dt><dd>待确认</dd></div><div><dt>{findingCount.ambiguous}</dt><dd>模糊点</dd></div><div><dt>{findingCount.risks}</dt><dd>风险</dd></div></dl>
          </aside>}
      </section>

      {result && <section className="analysis-result paper-panel">
        <div className="analysis-heading"><div><span className="ai-glyph">A</span><div><h2>AI 初步分析</h2><p>从一句模糊需求中识别出了可执行前必须对齐的信息。</p></div></div><ConfirmationStatus status={result.analysis.confirmation_status} /></div>
        <div className="analysis-columns">
          <AnalysisColumn tone="green" icon="✓" title="已确认的信息" items={result.analysis.payload.confirmed_information.map((i) => zh(i.description))} />
          <AnalysisColumn tone="amber" icon="?" title="需要进一步确认" items={result.analysis.payload.missing_information.map((i) => zh(i.description))} />
          <AnalysisColumn tone="purple" icon="◇" title="模糊点" items={result.analysis.payload.ambiguities.map((i) => zh(i.description))} />
          <AnalysisColumn tone="red" icon="!" title="潜在风险" items={result.analysis.payload.risks.map((i) => zh(i.description))} />
        </div>
        <div className="analysis-footer"><p>AI 仅提供建议。下一步由你回答问题并确认需求内容。</p><button className="button primary" onClick={() => router.push("/alignment")}>开始需求对齐 →</button></div>
      </section>}
    </main>
  );
}

function AnalysisColumn({ tone, icon, title, items }: { tone: string; icon: string; title: string; items: string[] }) {
  return <div className={`analysis-column ${tone}`}><h3><span>{icon}</span>{title}<b>{items.length}</b></h3><ul>{items.map((item) => <li key={item}><span>{icon}</span>{item}</li>)}</ul></div>;
}
