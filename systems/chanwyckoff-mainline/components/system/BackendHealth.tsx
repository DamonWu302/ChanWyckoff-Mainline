"use client";

import { useEffect, useState } from "react";
import { Status } from "@/components/ui/Status";

type HealthState = "checking" | "ok" | "offline";

export function BackendHealth() {
  const [state, setState] = useState<HealthState>("checking");

  useEffect(() => {
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 1800);

    fetch(`${baseUrl}/api/health`, { signal: controller.signal })
      .then((response) => {
        setState(response.ok ? "ok" : "offline");
      })
      .catch(() => setState("offline"))
      .finally(() => window.clearTimeout(timeout));

    return () => {
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, []);

  if (state === "checking") {
    return <Status variant="info">api checking</Status>;
  }

  if (state === "ok") {
    return <Status variant="good">api healthy</Status>;
  }

  return <Status variant="warn">api offline</Status>;
}

