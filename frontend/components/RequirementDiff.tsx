import type { RequirementDiffEntry } from "@/lib/types";
import { zh } from "@/lib/copy";

const config = {
  ADDED: ["+", "新增"],
  REMOVED: ["−", "移除"],
  MODIFIED: ["△", "调整"],
  UNCHANGED: ["=", "保持"],
} as const;

const fieldLabels: Record<string, string> = {
  "scope.project_specific_test": "范围 · 项目场景测试",
  "scope.additional_test_cases": "范围 · 补充与边界 Case",
  "scope.top_2_final_validation": "范围 · Top 2 Final Validation",
  "additional_fields.candidate_models[Doubao 1.5]": "候选模型 · 豆包 1.5",
  "acceptance_criteria.final_recommendation": "验收标准 · 最终推荐",
  metrics: "评估维度",
};

export function RequirementDiff({ entries }: { entries: RequirementDiffEntry[] }) {
  return (
    <div className="requirement-diff">
      {entries.map((entry) => {
        const [mark, label] = config[entry.category];
        return (
          <div className={`diff-line ${entry.category.toLowerCase()}`} key={entry.id}>
            <span className="diff-mark">{mark}</span>
            <div><b>{zh(entry.explanation)}</b><small>{fieldLabels[entry.field_path] ?? entry.field_path}</small></div>
            <span className="diff-label">{label}</span>
          </div>
        );
      })}
    </div>
  );
}
