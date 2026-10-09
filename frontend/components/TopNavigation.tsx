"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";

const links = [
  { href: "/", label: "工作台", active: ["/"] },
  { href: "/execution", label: "项目", active: ["/alignment", "/execution", "/review"] },
  { href: "/new", label: "模板", active: [] },
  { href: "/", label: "帮助", active: [] },
];

export function TopNavigation() {
  const pathname = usePathname();
  const [mode, setMode] = useState<string>("连接中");
  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((response) => response.json())
      .then((data) => setMode(data.mode ?? "未配置"))
      .catch(() => setMode("离线"));
  }, []);
  return (
    <header className="topbar">
      <Link href="/" className="brand" aria-label="Requirement Alignment Engine 首页">
        <span className="brand-mark">R</span>
        <span>Requirement<br />Alignment Engine</span>
      </Link>
      <nav className="main-nav" aria-label="主导航">
        {links.map(({ href, label, active }) => (
          <Link key={label} href={href} className={active.includes(pathname) ? "active" : ""}>{label}</Link>
        ))}
      </nav>
      <div className="nav-tools">
        <span className={`mode-badge ${mode.toLowerCase()}`}>{mode}</span>
        <label className="search-box"><span>⌕</span><input aria-label="搜索" placeholder="搜索项目、关键词…" /></label>
        <button className="icon-button" aria-label="通知">♢</button>
        <span className="avatar">Y</span>
        <span className="user-name">Yihan</span>
      </div>
    </header>
  );
}
