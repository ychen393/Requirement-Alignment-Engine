"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import {currentSession,listKnowledge,logOut} from "@/lib/supabaseAuth";
type Doc={id:string;title:string;kind:string};
export default function KnowledgePage(){
 const [ready,setReady]=useState(false);
 const [email,setEmail]=useState<string|null>(null);
 const [org,setOrg]=useState("");
 const [docs,setDocs]=useState<Doc[]>([]);
 const [error,setError]=useState("");
 const [busy,setBusy]=useState(false);
 useEffect(()=>{void currentSession().then(s=>setEmail(s?.email??(s?"Authenticated user":null))).finally(()=>setReady(true));},[]);
 async function search(){
  setBusy(true);setError("");
  try{setDocs(await listKnowledge(org));}
  catch(e){setError(e instanceof Error?e.message:"Knowledge read failed");}
  finally{setBusy(false);}
 }
 if(!ready)return <main className="page-shell compact-page">正在检查登录状态…</main>;
 if(!email)return <main className="page-shell compact-page"><h1>企业知识库</h1><p>请先登录。</p><Link href="/login">前往登录</Link></main>;
 return <main className="page-shell compact-page">
  <section className="new-header"><span className="eyebrow">Enterprise Knowledge</span><h1>企业知识库</h1><p>已登录：{email}</p></section>
  <section className="paper-panel" style={{padding:28}}>
   <label htmlFor="org-id">组织 UUID（开发验收专用）</label>
   <input id="org-id" value={org} onChange={e=>setOrg(e.target.value)} placeholder="需要管理员授予成员权限" style={{display:"block",width:"100%",maxWidth:550,padding:12,margin:"12px 0"}}/>
   <div style={{display:"flex",gap:12}}>
    <button disabled={busy||!/^[0-9a-f-]{36}$/i.test(org)} onClick={()=>void search()}>{busy?"查询中…":"查询已授权文档"}</button>
    <button onClick={()=>{void logOut().then(()=>location.assign("/login"));}}>退出登录</button>
   </div>
   {error&&<p role="alert">{error}</p>}
   {docs.length===0?<p>暂无可访问文档。新数据库没有自动授予任何资料权限。</p>:
    <ul>{docs.map(d=><li key={d.id}>{d.title} · {d.kind}</li>)}</ul>}
   <p>此页面是权限联调入口，尚未提供上传、编辑或 Proposal 引用功能。</p>
  </section>
 </main>;
}
