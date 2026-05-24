"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { navigationItems } from "@/lib/navigation";
import { cn } from "@/lib/cn";

type AppShellProps = {
  children: ReactNode;
  note: string;
};

export function AppShell({ children, note }: AppShellProps) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/">
          <span className="brand-mark">CW</span>
          <span>
            <span className="brand-title">ChanWyckoff</span>
            <span className="brand-sub">Mainline Desk</span>
          </span>
        </Link>
        <nav aria-label="主导航" className="nav-group">
          <div className="nav-label">Workspaces</div>
          {navigationItems.map((item) => {
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link className={cn("nav-link", active && "active")} href={item.href} key={item.href}>
                {item.label}
                <span className="nav-kbd">{item.kbd}</span>
              </Link>
            );
          })}
        </nav>
        <div className="system-note">{note}</div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}

