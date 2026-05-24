"use client";

import type { ReactNode } from "react";
import { useState } from "react";
import { cn } from "@/lib/cn";

export type TabItem = {
  id: string;
  label: string;
  panel: ReactNode;
};

type TabsProps = {
  items: TabItem[];
  defaultValue?: string;
};

export function Tabs({ items, defaultValue }: TabsProps) {
  const [active, setActive] = useState(defaultValue ?? items[0]?.id);

  return (
    <>
      <div className="tabs">
        {items.map((item) => (
          <button
            className={cn("tab", active === item.id && "active")}
            key={item.id}
            onClick={() => setActive(item.id)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </div>
      {items.map((item) => (
        <section hidden={active !== item.id} key={item.id}>
          {item.panel}
        </section>
      ))}
    </>
  );
}

