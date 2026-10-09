"use client";

import { useState } from "react";
import type { AcceptanceCriterion, CriterionEvaluation } from "@/lib/types";
import { zh } from "@/lib/copy";

export function EvidenceRow({ criterion, result }: { criterion: AcceptanceCriterion; result?: CriterionEvaluation }) {
  const [open, setOpen] = useState(false);
  const [adding, setAdding] = useState(false);
  const [note, setNote] = useState("");
  const passed = result?.status === "PASS";
  return (
    <div className="evidence-row">
      <span className={`evidence-status ${passed ? "pass" : "pending"}`}>{passed ? "✓" : "○"}</span>
      <div className="evidence-main">
        <b>{zh(criterion.title)}</b>
        <small>{zh(result?.explanation ?? criterion.description)}</small>
        {open && <div className="evidence-detail">{note || (result?.evidence.length ? result.evidence.join(" · ") : "尚未提供可验证证据")}</div>}
        {adding && <div className="evidence-add"><input value={note} onChange={(e) => setNote(e.target.value)} placeholder="粘贴证据链接或说明" /><button onClick={() => { setAdding(false); setOpen(true); }}>保存草稿</button></div>}
      </div>
      <div className="evidence-actions">
        <button onClick={() => setOpen(!open)}>查看证据</button>
        {!passed && <button className="accent" onClick={() => setAdding(!adding)}>补充证据</button>}
      </div>
    </div>
  );
}
