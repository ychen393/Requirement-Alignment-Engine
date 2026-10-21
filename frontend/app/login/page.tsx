"use client";
import {useEffect,useState} from "react";
import {useRouter} from "next/navigation";
import {authConfigured,currentSession,signIn,signUp} from "@/lib/supabaseAuth";
export default function LoginPage(){
 const router=useRouter();
 const [email,setEmail]=useState("");
 const [password,setPassword]=useState("");
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState("");
 const [notice,setNotice]=useState("");
 useEffect(()=>{void currentSession().then(s=>{if(s)router.replace("/knowledge")});},[router]);
 async function submit(kind:"login"|"signup"){
  setError("");setNotice("");setBusy(true);
  try{
   if(kind==="signup"){await signUp(email,password);setNotice("Registration submitted. Check your email if confirmation is required.");}
   else{await signIn(email,password);router.push("/knowledge");}
  }catch(e){setError(e instanceof Error?e.message:"Authentication failed");}
  finally{setBusy(false);}
 }
 return <main className="page-shell compact-page">
  <section className="new-header"><span className="eyebrow">Enterprise Knowledge</span><h1>顾问登录</h1><p>使用 Supabase Auth 登录。登录并不自动授予企业知识库权限。</p></section>
  <section className="paper-panel" style={{maxWidth:540,padding:28}}>
  {!authConfigured()?<p role="alert">尚未配置 Supabase 公共连接参数。</p>:
   <form onSubmit={e=>{e.preventDefault();void submit("login");}}>
    <label htmlFor="email">邮箱</label>
    <input id="email" type="email" autoComplete="email" required value={email} onChange={e=>setEmail(e.target.value)} style={{display:"block",width:"100%",padding:12,margin:"8px 0 20px"}}/>
    <label htmlFor="password">密码</label>
    <input id="password" type="password" autoComplete="current-password" minLength={6} required value={password} onChange={e=>setPassword(e.target.value)} style={{display:"block",width:"100%",padding:12,margin:"8px 0 20px"}}/>
    <div style={{display:"flex",gap:12}}>
     <button type="submit" disabled={busy}>登录</button>
     <button type="button" disabled={busy} onClick={()=>void submit("signup")}>注册测试账号</button>
    </div>
    {error&&<p role="alert">{error}</p>}
    {notice&&<p role="status">{notice}</p>}
   </form>}
  <p>仅使用模拟资料测试。注册成功后仍需管理员分配组织成员和文档授权。</p>
  </section>
 </main>;
}
