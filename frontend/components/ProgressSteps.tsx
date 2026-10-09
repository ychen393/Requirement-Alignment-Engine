const steps = ["需求分析", "澄清问题", "需求对齐", "执行计划"];

export function ProgressSteps({ current }: { current: number }) {
  return (
    <ol className="progress-steps" aria-label="需求进度">
      {steps.map((step, index) => (
        <li key={step} className={index + 1 <= current ? "active" : ""}>
          <span>{index + 1}</span>{step}
        </li>
      ))}
    </ol>
  );
}
