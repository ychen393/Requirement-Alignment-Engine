"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";
const links = [
  {href:"/",label:"工作台"},
  {href:"/new",label:"Client Brief"},
  {href:"/approach",label:"Consulting Approach"},
  {href:"/proposal",label:"Proposal Studio"},
  {href:"/knowledge",label:"知识库"},
  {href:"/login",label:"登录"}
];
export function TopNavigation() {
  const pathname=usePathname();
  const [mode,setMode]=useState("连接中");
  useEffect(()=>{fetch(`${API_BASE}/health`).then(r=>r.json()).then(d=>setMode(d.mode??"未配置")).catch(()=>setMode("离线"));},[]);
  return <header className="topbar"><Link href="/" className="brand"><span className="brand-mark">R</span><span>Requirement<br/>Alignment Engine</span></Link>
  <nav className="main-nav" aria-label="主导航">{links.map(x=><Link key={x.href} href={x.href} className={pathname===x.href?"active":""}>{x.label}</Link>)}</nav>
  <div className="nav-tools"><span className={`mode-badge ${mode.toLowerCase()}`}>{mode}</span><span className="user-name">Consulting MVP · Preview</span></div></header>;
}
