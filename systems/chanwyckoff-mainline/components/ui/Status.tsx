import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type StatusVariant = "default" | "good" | "info" | "warn" | "danger";

type StatusProps = {
  children: ReactNode;
  variant?: StatusVariant;
  className?: string;
};

export function Status({ children, variant = "default", className }: StatusProps) {
  return <span className={cn("status", variant !== "default" && variant, className)}>{children}</span>;
}

