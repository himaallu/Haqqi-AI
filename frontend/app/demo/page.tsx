import type { Metadata } from "next";

import { DemoLoader } from "./demo-loader";

export const metadata: Metadata = {
  title: "Haqqi demo",
  description: "Haqqi pitch demo: your rights at work in the UAE, in your language.",
};

/** The Sheraa pitch demo (docs/demo/LOVABLE_PROMPT.md, built here instead): separate from the main flow at /[lang]. */
export default function DemoPage() {
  return <DemoLoader />;
}
