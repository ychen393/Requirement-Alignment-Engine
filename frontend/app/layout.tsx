import type { Metadata } from "next";
import { TopNavigation } from "@/components/TopNavigation";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Requirement Alignment Engine",
    template: "%s · Requirement Alignment Engine",
  },
  applicationName: "Requirement Alignment Engine",
  description: "从模糊需求到可执行计划与可验证结果的 AI 需求对齐工作台。",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>
        <TopNavigation />
        {children}
      </body>
    </html>
  );
}
