import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type PanelProps = {
  title?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
};

export function Panel({ title, action, children, className, bodyClassName }: PanelProps) {
  return (
    <section className={cn("panel", className)}>
      {(title || action) && (
        <div className="panel-header">
          {typeof title === "string" ? <h2>{title}</h2> : title}
          {action}
        </div>
      )}
      <div className={cn("panel-body", bodyClassName)}>{children}</div>
    </section>
  );
}

