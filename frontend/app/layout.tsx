import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Haqqi",
  description: "Understand your work rights in the UAE, in your own language.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col">{children}</body>
    </html>
  );
}
