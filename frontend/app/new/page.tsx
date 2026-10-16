"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ProgressSteps } from "@/components/ProgressSteps";
import { analyzeRequirement,saveWorkspace } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";
export default function ClientBriefPage(){
 const router=useRouter(),[text,setText]=useState(""),[result,setResult]=useState<AnalyzeResponse>(),
 [loading,setLoading]=useState(false),[error,setError]=useState("");
 async function analyze(){setLoading(true);setError("");try{
 const data=await analyzeRequirement(text);setResult(data);saveWorkspace({analysis:data,requirementV1:undefined,approach:undefined,consultingProposal:undefined});
 }catch(e){setError(e instanceof Error?e.message:"分析失败")}finally{setLoading(false)}}
 return <main className="page-shell compact-page"><div className="page-top"><ProgressSteps current={result?2:1}/></div>
 <section className="new-header"><span className="eyebrow">01 · Client Brief Intake</span><h1>新建客户 Brief</h1><p>粘贴脱敏客户需求。AI 会区分已知信息与待确认假设，而不是直接生成执行计划。</p></section>
 <section className="request-entry-grid"><div className="request-composer">
 <label htmlFor="brief">原始客户需求</label><textarea id="brief" maxLength={2000} value={text} onChange={e=>setText(e.target.value)} placeholder="例如：某护肤品牌希望提高年轻消费者的品牌认知，但尚未确定预算和成功标准。"/>
 <span className="character-count">{text.length}/2000</span>
 <button className="button primary centered" disabled={loading||!text.trim()} onClick={analyze}>{loading?"分析中…":"分析 Client Brief →"}</button>
 {error&&<p role="alert" className="error-message">{error}</p>}</div>
 <aside className="paper-panel" style={{padding:24}}><h2>本阶段关注</h2><p>业务目标、问题界定、客户边界、缺失信息、可验证的交付期待。</p><p>注意：DEMO 模式可能返回固定样例，不能代表对输入 Brief 的真实分析。</p></aside></section>
 {result&&<section className="paper-panel" style={{padding:28,marginTop:24}}>
 <h2>初步分析 · {result.mode}</h2>
 <p>已知信息：{result.analysis.payload.confirmed_information.length} 项 · 待确认：{result.analysis.payload.missing_information.length} 项 · 风险：{result.analysis.payload.risks.length} 项</p>
 <p>{result.mode==="DEMO"?"当前返回的是固定演示数据，后续结果不代表客户真实需求。":"请审核 AI 推断，不要将其视为客户已确认事实。"}</p>
 <button className="button primary" onClick={()=>router.push("/alignment")}>进入澄清与需求确认 →</button></section>}
 </main>
}
