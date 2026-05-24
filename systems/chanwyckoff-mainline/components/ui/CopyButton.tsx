"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";

type CopyButtonProps = {
  text: string;
  children: string;
};

export function CopyButton({ text, children }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text);
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 900);
  }

  return (
    <Button className={copied ? "is-copied" : undefined} onClick={handleCopy} type="button">
      {copied ? "已复制" : children}
    </Button>
  );
}

