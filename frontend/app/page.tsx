import Link from "next/link";
export default function HomePage() {
  return <main className="page-shell workbench">
    <section className="hero"><div className="hero-copy">
      <span className="paper-label">Consulting & Agency Workspace</span>
      <h1>从模糊 Client Brief<br/>到可审阅的客户方案</h1>
      <p>澄清客户真正想解决的问题，形成确认过的需求，设计咨询方法论并制作 Proposal。</p>
      <Link className="button primary" href="/new">＋ 创建客户 Brief</Link>
    </div><div className="hero-illustration" aria-hidden="true">
      <div className="note-card note-a"><b>Client Brief</b><i/></div><div className="note-card note-b"><b>Clarification</b><i/></div>
      <div className="note-card note-c"><b>Approach</b><i/></div><div className="note-card note-d"><b>Proposal</b><i/></div>
      <div className="note-card note-e"><b>Client Review</b><i/></div>
      <svg viewBox="0 0 500 210" role="presentation"><path d="M35 125 C120 55 170 150 248 80 S370 40 460 105"/><circle cx="130" cy="87" r="4"/><circle cx="248" cy="80" r="14"/><circle cx="365" cy="58" r="4"/></svg>
    </div></section>
    <section className="paper-panel" style={{padding:32,marginTop:24}}>
      <h2>你的咨询流程</h2><p>01 Client Brief → 02 需求澄清 → 03 需求确认 → 04 Consulting Approach → 05 Proposal Studio → 06 Client Preview</p>
      <p>当前为开发预览：尚未连接真实项目数据库。所有演示示例需明确标注为 DEMO，不能当作真实历史项目。</p>
      <Link href="/new" className="button primary">开始新项目 →</Link>
    </section>
  </main>;
}
