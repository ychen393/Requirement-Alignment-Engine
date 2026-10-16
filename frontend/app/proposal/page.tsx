"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import {generateConsultingProposal,loadWorkspace,previewConsultingProposal,saveWorkspace} from "@/lib/api";
import type {ConsultingProposalDocument} from "@/lib/types";
import {ProgressSteps} from "@/components/ProgressSteps";
export default function ProposalStudio(){
 const [doc,setDoc]=useState<ConsultingProposalDocument>(),[html,setHtml]=useState("");
 const [loading,setLoading]=useState(false),[error,setError]=useState("");
 const [available,setAvailable]=useState(false);
 useEffect(()=>{const w=loadWorkspace();setAvailable(Boolean(w.requirementV1&&w.approach));setDoc(w.consultingProposal)},[]);
 async function generate(){const w=loadWorkspace();if(!w.requirementV1||!w.approach)return;setLoading(true);setError("");try{
 const id=w.analysis?.raw_requirement.payload.id ?? crypto.randomUUID();
 const result=await generateConsultingProposal(id,w.requirementV1,w.approach.payload);setDoc(result);setHtml("");saveWorkspace({consultingProposal:result});
 }catch(e){setError(e instanceof Error?e.message:"生成失败")}finally{setLoading(false)}}
 function editSummary(value:string){setDoc(d=>d?{...d,executive_summary:value,status:"REVIEW_REQUIRED"}:d);setHtml("")}
 function editHeading(index:number,value:string){setDoc(d=>d?{...d,status:"REVIEW_REQUIRED",sections:d.sections.map((s,i)=>index===i?{...s,heading:value}:s)}:d);setHtml("")}
 function persist(){if(doc)saveWorkspace({consultingProposal:doc})}
 async function preview(){if(!doc)return;setLoading(true);setError("");try{persist();setHtml(await previewConsultingProposal(doc))}catch(e){setError(e instanceof Error?e.message:"预览失败")}finally{setLoading(false)}}
 function download(){if(!html)return;const url=URL.createObjectURL(new Blob([html],{type:"text/html;charset=utf-8"}));const a=document.createElement("a");a.href=url;a.download="consulting-proposal-DRAFT.html";a.click();URL.revokeObjectURL(url)}
 return <main className="page-shell compact-page"><div className="page-top"><ProgressSteps current={5}/></div>
 <section className="new-header"><span className="eyebrow">05 · Proposal Studio</span><h1>客户方案工作台</h1><p>结构化生成、人工编辑与 HTML 草稿预览。正式客户审核与数据持久化尚未上线。</p></section>
 {!available?<section className="paper-panel" style={{padding:24}}><p>还没有确认的需求和 Consulting Approach。</p><Link href="/new">开始 Client Brief →</Link></section>:
 <section className="paper-panel" style={{padding:24}}><button className="button primary" onClick={generate} disabled={loading}>{loading?"处理中…":doc?"重新生成 Proposal":"生成客户 Proposal →"}</button>
 {error&&<p role="alert" className="error-message">{error}</p>}</section>}
 {doc&&<section className="paper-panel" style={{padding:24,marginTop:20}}>
 <p><b>DRAFT / 仅供内部审核</b> · Proposal V{doc.version_number}</p><h2>{doc.title}</h2>
 <label>Executive Summary<textarea style={{display:"block",width:"100%",minHeight:110,padding:12}} value={doc.executive_summary} onChange={e=>editSummary(e.target.value)} onBlur={persist}/></label>
 {doc.sections.map((s,i)=><div key={s.id} style={{padding:"16px 0",borderBottom:"1px solid #ddd"}}>
 <label>Section {i+1}<input value={s.heading} onChange={e=>editHeading(i,e.target.value)} onBlur={persist} style={{display:"block",width:"100%",padding:10}}/></label>
 {s.blocks.map((b,j)=><p key={j}>{b.type==="BULLETS"?b.items.join(" · "):b.text}</p>)}</div>)}
 <div style={{display:"flex",gap:12,flexWrap:"wrap",paddingTop:20}}>
 <button className="button primary" onClick={preview} disabled={loading}>生成 HTML 预览 →</button>
 <button className="button" disabled={!html} onClick={download}>下载带 DRAFT 标记的 HTML</button></div>
 </section>}
 {html&&<section className="paper-panel" style={{padding:20,marginTop:20}}><h2>06 · Client Preview（草稿）</h2><iframe title="Proposal HTML draft" sandbox="" srcDoc={html} style={{width:"100%",height:650,border:"1px solid #ddd",background:"white"}}/></section>}
 </main>;
}
