"use client";

import dynamic from "next/dynamic";

// Browser only: the demo reads localStorage, the URL and the phone's voices on its first render.
const DemoApp = dynamic(() => import("@/components/demo/demo-app").then((m) => m.DemoApp), { ssr: false });

export function DemoLoader() {
  return <DemoApp />;
}
