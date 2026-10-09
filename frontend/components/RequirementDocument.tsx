"use client";

import type { RequirementVersion } from "@/lib/types";
import { zh } from "@/lib/copy";
import { ConfirmationStatus } from "./ConfirmationStatus";

function EditableList({ items, onChange }: { items: string[]; onChange?: (items: string[]) => void }) {
  return (
    <ul className="editable-list">
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>
          <span>•</span>
          {onChange ? (
            <input
              value={zh(item)}
              aria-label={`编辑条目 ${index + 1}`}
              onChange={(event) => {
                const next = [...items];
                next[index] = event.target.value;
                onChange(next);
              }}
            />
          ) : zh(item)}
        </li>
      ))}
    </ul>
  );
}

export function RequirementDocument({
  requirement,
  onChange,
}: {
  requirement: RequirementVersion;
  onChange?: (next: RequirementVersion) => void;
}) {
  const set = <K extends keyof RequirementVersion>(key: K, value: RequirementVersion[K]) =>
    onChange?.({ ...requirement, [key]: value });
  return (
    <article className="requirement-document">
      <div className="document-heading">
        <div><span className="eyebrow">需求内容</span><h2>Requirement V{requirement.version_number}</h2></div>
        <ConfirmationStatus status="AI_SUGGESTED" />
      </div>
      <section className="document-section green-rule">
        <div className="section-title"><strong>目标</strong><em>AI 建议</em></div>
        {onChange ? <textarea value={zh(requirement.objective)} onChange={(e) => set("objective", e.target.value)} /> : <p>{zh(requirement.objective)}</p>}
      </section>
      <section className="document-section green-rule">
        <div className="section-title"><strong>范围</strong><em>AI 建议</em></div>
        <EditableList items={requirement.scope} onChange={onChange ? (v) => set("scope", v) : undefined} />
      </section>
      <section className="document-section orange-rule">
        <div className="section-title"><strong>不包含</strong></div>
        <EditableList items={requirement.out_of_scope} onChange={onChange ? (v) => set("out_of_scope", v) : undefined} />
      </section>
      <section className="document-section">
        <div className="section-title"><strong>约束</strong></div>
        <EditableList items={requirement.constraints} onChange={onChange ? (v) => set("constraints", v) : undefined} />
      </section>
      <section className="document-section green-rule">
        <div className="section-title"><strong>预期交付</strong><em>AI 建议</em></div>
        <EditableList items={requirement.expected_outputs} onChange={onChange ? (v) => set("expected_outputs", v) : undefined} />
      </section>
      <section className="document-section criteria-section">
        <div className="section-title"><strong>验收标准</strong></div>
        {requirement.acceptance_criteria.map((criterion) => (
          <div className="criterion-line" key={criterion.id}>
            <span className="empty-check" />
            <div><b>{zh(criterion.title)}</b><small>{zh(criterion.description)}</small></div>
            <em>AI 建议</em>
          </div>
        ))}
      </section>
    </article>
  );
}
