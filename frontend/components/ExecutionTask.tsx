import type { Task } from "@/lib/types";
import { zh } from "@/lib/copy";

const statusCopy = {
  DONE: ["✓", "完成"],
  IN_PROGRESS: ["△", "进行中"],
  BLOCKED: ["!", "阻塞"],
  NOT_STARTED: ["○", "未开始"],
  INVALIDATED: ["×", "已失效"],
} as const;

type ChangeTag = { label: string; tone: "existing" | "modified" | "new" | "rework" };

export function ExecutionTask({ task, changeTag }: { task: Task; changeTag?: ChangeTag }) {
  const [icon, label] = statusCopy[task.status];
  return (
    <div className={`execution-task ${task.status.toLowerCase()}`}>
      <span className="task-order">{task.execution_order}</span>
      <span className="task-icon">{icon}</span>
      <div><b>{zh(task.title)}{changeTag && <em className={`task-origin ${changeTag.tone}`}>{changeTag.label}</em>}</b><small>{zh(task.description)}</small></div>
      <span className="task-state">{label}</span>
    </div>
  );
}
