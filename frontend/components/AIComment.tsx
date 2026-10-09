import type { ReactNode } from "react";

export function AIComment({ title = "AI 建议", children }: { title?: string; children: ReactNode }) {
  return (
    <aside className="ai-comment">
      <div className="ai-comment-label"><span>AI</span>{title}</div>
      <div className="ai-comment-body">{children}</div>
    </aside>
  );
}
