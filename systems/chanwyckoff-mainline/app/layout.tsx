import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChanWyckoff Mainline",
  description: "缠威主线系统：从大盘到工程化三买的操作工作台",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}

