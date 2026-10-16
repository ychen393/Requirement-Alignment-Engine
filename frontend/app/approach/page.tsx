"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import {useRouter} from "next/navigation";
import {generateConsultingApproach,loadWorkspace,saveWorkspace} from "@/lib/api";
import type {ConsultingApproach,Proposal,RequirementVersion} from "@/lib/types";
import {ProgressSteps} from "@/components/ProgressSteps";
export default function ApproachPage(){
 const router=useRouter();
 const [requirement,setRequirement]=useState<Proposal<RequirementVersion>>();
 const [approach,setApproach]=useState<ConsultingApproach>();
 const [loading,setLoading]=useState(false),[error,setError]=useState("");
 useEffect(()=>{const w=loadWorkspace();setRequirement(w.requirementV1);setApproach(w.approach?.payload)},[]);
 async function generate(){if(!requirement)return;setLoading(true);setError("");try{
 const result=await generateConsultingApproach(requirement);setApproach(result.proposal.payload);
 saveWorkspace({approach:result.proposal,consultingProposal:undefined});
 }catch(e){setError(e instanceof Error?e.message:"生成失败")}finally{setLoading(false)}}
 function update(i:number,field:"title"|"objective",value:string){setApproach(v=>v?{...v,workstreams:v.workstreams.map((w,j)=>i===j?{...w,[field]:value}:w)}:v)}
 function proceed(){if(!approach)return;saveWorkspace({approach:{confirmation_status:"AI_SUGGESTED",payload:approach},consultingProposal:undefined});router.push("/proposal")}
 return <main className="page-shell compact-page"><div className="page-top"><ProgressSteps current={4}/></div>
 <section className="new-header"><span className="eyebrow">04 · Consulting Approach</span><h1>设计咨询方法论</h1><p>根据确认的 Client Requirement 设计工作流、分析方法和交付物。方法论是建议，不是已完成的研究结论。</p></section>
 {!requirement?<section className="paper-panel" style={{padding:24}}><p>请先完成客户需求确认。</p><Link href="/new">从 Client Brief 开始 →</Link></section>:
 <section className="paper-panel" style={{padding:24}}><h2>需求版本 {requirement.payload.version_number}</h2><p>{requirement.payload.objective}</p>
 <button className="button primary" onClick={generate} disabled={loading}>{loading?"设计中…":approach?"重新生成方法论":"生成 Consulting Approach →"}</button>
 {error&&<p role="alert" className="error-message">{error}</p>}</section>}
 {approach&&<section className="paper-panel" style={{padding:24,marginTop:20}}>
 <h2>建议方法论 · 可修改</h2><p>{approach.rationale}</p>
 {approach.workstreams.map((w,i)=><div key={w.id} style={{borderTop:"1px solid #ddd",padding:"20px 0"}}>
 <label>Workstream {i+1}<input style={{display:"block",width:"100%",padding:10,margin:"8px 0"}} value={w.title} onChange={e=>update(i,"title",e.target.value)}/></label>
 <label>目标<input style={{display:"block",width:"100%",padding:10,margin:"8px 0"}} value={w.objective} onChange={e=>update(i,"objective",e.target.value)}/></label>
 <p><b>方法：</b>{w.methods.join("、")}</p><p><b>交付物：</b>{w.deliverables.join("、")}</p><p><b>所需资料：</b>{w.data_required.join("、")||"待确认"}</p></div>)}
 <p>未知条件：{approach.unknowns.join("；")||"暂无"}</p>
 <button className="button primary" onClick={proceed}>使用此方法论制作 Proposal →</button></section>}
 </main>;
}
