import { notFound } from "next/navigation";
import { DesignSystemPreview } from "@/components/design-system/DesignSystemPreview";

export default function Page() {
  if (process.env.NODE_ENV !== "development") {
    notFound();
  }

  return <DesignSystemPreview />;
}

