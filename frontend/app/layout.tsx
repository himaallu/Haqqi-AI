import type { Metadata, Viewport } from "next";

import { WakeBackend } from "@/components/wake-backend";

import { fontVariables } from "./fonts";
import "./globals.css";

export const metadata: Metadata = {
  title: "Haqqi",
  description: "Understand your work rights in the UAE, in your own language.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1 };

// The [lang] layout sets lang/dir on its own wrapper and mirrors them onto <html> on the client.
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" dir="ltr" className={`h-full antialiased ${fontVariables}`}>
      <body className="flex min-h-full flex-col">
        <WakeBackend />
        {children}
      </body>
    </html>
  );
}
