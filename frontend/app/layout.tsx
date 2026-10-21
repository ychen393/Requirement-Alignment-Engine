import type { Metadata } from "next";
import { TopNavigation } from "@/components/TopNavigation";
import "./globals.css";
export const metadata: Metadata = {
 title:{default:"Requirement Alignment Engine",template:"%s · Requirement Alignment Engine"},
 applicationName:"Requirement Alignment Engine",
 description:"咨询顾问的 Client Brief 澄清、需求对齐与 Proposal 制作工作台。"
};
export default function RootLayout({children}:Readonly<{children:React.ReactNode}>) {
 return <html lang="zh-CN"><body><TopNavigation/>{children}</body></html>;
}
