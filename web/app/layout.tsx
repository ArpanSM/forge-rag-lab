import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: {
    default: "Forge RAG Lab — evidence-first retrieval",
    template: "%s · Forge RAG Lab",
  },
  description:
    "Chat with versioned Helios documentation, inspect claim-level citations and compare the baseline and fixed RAG pipelines.",
  applicationName: "Forge RAG Lab",
  authors: [{ name: "Arpan Mahapatra", url: "https://github.com/ArpanSM" }],
  keywords: ["RAG", "retrieval", "citations", "evaluation", "Helios"],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f5f1e8",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col">
        <a href="#main-content" className="skip-link">
          Skip to content
        </a>
        <SiteHeader />
        <main id="main-content" className="flex-1">
          {children}
        </main>
        <SiteFooter />
      </body>
    </html>
  );
}
