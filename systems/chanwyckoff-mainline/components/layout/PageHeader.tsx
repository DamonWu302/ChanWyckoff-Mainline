import type { ReactNode } from "react";

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  lead: string;
  actions?: ReactNode;
};

export function PageHeader({ eyebrow, title, lead, actions }: PageHeaderProps) {
  return (
    <header className="topbar">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p className="lead">{lead}</p>
      </div>
      {actions && <div className="actions">{actions}</div>}
    </header>
  );
}

