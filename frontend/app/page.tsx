import Link from "next/link";

const projects = [
  { icon: "▣", name: "模型能力 Benchmark", status: "执行中", tone: "blue", version: "V2", progress: "4 / 12", note: "最新变更：新增项目测试集与 Top 2 Final Validation", ago: "2 小时前" },
  { icon: "▤", name: "营销活动数据分析", status: "待确认", tone: "orange", version: "V1", progress: "2 / 8", note: "还有 2 个关键问题未确认", ago: "5 小时前" },
  { icon: "▦", name: "客户支持助手评估", status: "执行中", tone: "blue", version: "V1", progress: "6 / 10", note: "调整评估标准", ago: "1 天前" },
  { icon: "◆", name: "产品功能调研", status: "已完成", tone: "green", version: "V1", progress: "8 / 8", note: "—", ago: "3 天前" },
];

export default function WorkbenchPage() {
  return (
    <main className="workbench page-shell">
      <section className="hero">
        <div className="hero-copy">
          <span className="paper-label">从模糊需求到可执行计划</span>
          <h1>让每一个需求<br />都说得清楚、做得到、验得了</h1>
          <p>把领导、客户或项目方的模糊需求，<br />转化为清晰的需求、可执行的计划和可验证的结果。</p>
          <Link href="/new" className="button primary">＋ 新建需求</Link>
        </div>
        <div className="hero-illustration" aria-hidden="true">
          <div className="note-card note-a"><b>模糊需求</b><i /></div>
          <div className="note-card note-b"><b>澄清问题</b><i /></div>
          <div className="note-card note-c"><b>执行计划</b><i /></div>
          <div className="note-card note-d"><b>需求变更</b><i /></div>
          <div className="note-card note-e"><b>验收完成</b><i /></div>
          <svg viewBox="0 0 500 210" role="presentation"><path d="M35 125 C120 55 170 150 248 80 S370 40 460 105" /><circle cx="130" cy="87" r="4"/><circle cx="248" cy="80" r="14"/><circle cx="365" cy="58" r="4"/></svg>
        </div>
      </section>

      <section className="home-grid">
        <div className="recent-panel paper-panel">
          <div className="panel-title"><h2>最近的需求</h2><span>按更新时间</span></div>
          <div className="project-list">
            {projects.map((project, index) => (
              <Link href={index === 0 ? "/execution" : "/new"} className="project-row" key={project.name}>
                <span className={`project-icon ${project.tone}`}>{project.icon}</span>
                <div className="project-name"><b>{project.name}</b><small>{project.note}</small></div>
                <span className={`status-pill ${project.tone}`}>{project.status}</span>
                <span className="version-text">{project.version}</span>
                <div className="progress-cell"><b>{project.progress}</b><span><i style={{ width: `${Number(project.progress.split(" /")[0]) / Number(project.progress.split("/")[1]) * 100}%` }} /></span></div>
                <time>{project.ago}</time>
              </Link>
            ))}
          </div>
          <Link href="/execution" className="text-link">查看全部需求 →</Link>
        </div>
        <aside className="attention-panel">
          <h2>需要你处理</h2>
          <span>2 个待办</span>
          <Link href="/execution" className="attention-item red"><b>模型能力 Benchmark</b><small>3 个需求变更待确认</small></Link>
          <Link href="/alignment" className="attention-item amber"><b>营销活动数据分析</b><small>2 个验收标准缺少证据</small></Link>
          <Link href="/alignment" className="attention-item blue"><b>客户支持助手评估</b><small>1 个澄清问题未回答</small></Link>
          <blockquote>“更少的反复沟通，<br />更清晰的执行和交付。”</blockquote>
        </aside>
      </section>
    </main>
  );
}
