const steps = ["Client Brief", "需求澄清", "需求确认", "Consulting Approach", "Proposal Studio", "客户预览"];
export function ProgressSteps({ current }: { current: number }) {
  return <ol className="progress-steps" aria-label="咨询方案进度">{steps.map((step, index) =>
    <li key={step} className={index+1<=current?"active":""}><span>{index+1}</span>{step}</li>)}</ol>;
}
