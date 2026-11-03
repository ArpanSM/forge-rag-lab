"use client";

import { Activity, MessageSquareText } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { API_MODE } from "@/lib/runtime";
import { SITE_REPO } from "@/lib/site";
import { cn } from "@/lib/utils";

function GithubMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" className={className}>
      <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55v-2.15c-3.2.7-3.87-1.36-3.87-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.03 1.75 2.7 1.25 3.36.95.1-.74.4-1.25.73-1.54-2.55-.29-5.23-1.28-5.23-5.68 0-1.26.45-2.28 1.18-3.09-.12-.29-.51-1.46.11-3.05 0 0 .96-.31 3.15 1.18a10.9 10.9 0 0 1 2.87-.39c.97 0 1.95.13 2.87.39 2.19-1.49 3.15-1.18 3.15-1.18.62 1.59.23 2.76.11 3.05.73.81 1.18 1.83 1.18 3.09 0 4.41-2.69 5.38-5.25 5.67.41.35.78 1.05.78 2.12v3.14c0 .3.21.66.8.55A11.5 11.5 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z" />
    </svg>
  );
}

const NAV_ITEMS = [
  {
    href: "/",
    label: "Chat",
    icon: MessageSquareText,
    isActive: (pathname: string) => pathname === "/" || pathname === "",
  },
  {
    href: "/health/",
    label: "Health report",
    icon: Activity,
    isActive: (pathname: string) => pathname.startsWith("/health"),
  },
];

export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-line/80 bg-paper/85 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <Link href="/" className="group flex min-w-0 items-center gap-2.5">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-ink shadow-sm transition-transform duration-300 group-hover:-rotate-3">
            <svg viewBox="0 0 32 32" aria-hidden="true" className="h-5 w-5">
              <path d="M9 7h14v4h-9.5v4H21v4h-7.5v6H9z" fill="#fffdf8" />
              <circle cx="23.5" cy="23.5" r="3" fill="#d65a31" />
            </svg>
          </span>
          <span className="min-w-0">
            <span className="block truncate font-display text-[1.08rem] font-semibold leading-tight tracking-[-0.01em] text-ink">
              Forge RAG Lab
            </span>
            <span className="eyebrow hidden text-[0.6rem] leading-tight sm:block">
              Helios reliability
            </span>
          </span>
        </Link>

        <div className="flex shrink-0 items-center gap-2">
          <nav
            aria-label="Primary"
            className="flex items-center gap-0.5 rounded-full border border-line bg-surface/70 p-0.5"
          >
            {NAV_ITEMS.map((item) => {
              const active = item.isActive(pathname);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-xs font-medium transition-colors sm:px-3 sm:text-[0.8rem]",
                    active
                      ? "bg-ink text-surface shadow-sm"
                      : "text-muted hover:bg-paper hover:text-ink",
                  )}
                >
                  <Icon aria-hidden="true" className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">{item.label}</span>
                  <span className="sr-only sm:hidden">{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <span
            className="hidden items-center gap-1.5 rounded-full border border-line bg-surface/70 px-2.5 py-1.5 font-mono text-[0.62rem] uppercase tracking-[0.1em] text-muted md:inline-flex"
            title={
              API_MODE === "mock"
                ? "Bundled fixtures are active. Set NEXT_PUBLIC_API_BASE to use the live API."
                : "The UI is querying the live FastAPI service."
            }
          >
            <span
              aria-hidden="true"
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                API_MODE === "mock" ? "bg-ember" : "bg-moss",
              )}
            />
            {API_MODE === "mock" ? "Mock fixtures" : "Live API"}
          </span>

          <a
            href={SITE_REPO}
            target="_blank"
            rel="noreferrer"
            aria-label="Forge RAG Lab on GitHub"
            className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-line bg-surface/70 text-muted transition-colors hover:border-line-strong hover:text-ink"
          >
            <GithubMark className="h-4 w-4" />
          </a>
        </div>
      </div>
    </header>
  );
}
