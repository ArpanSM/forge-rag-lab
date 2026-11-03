import { ArrowUpRight } from "lucide-react";
import { SITE_REPO } from "@/lib/site";

export function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-line/80">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-7 text-xs text-muted sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <p>
          Synthetic Helios corpus · No real customer data.{" "}
          <span className="hidden sm:inline">Built as a static Next.js export.</span>
        </p>
        <div className="flex items-center gap-4">
          <a
            className="inline-flex items-center gap-1 transition-colors hover:text-ink"
            href={`${SITE_REPO}#readme`}
            target="_blank"
            rel="noreferrer"
          >
            Documentation
            <ArrowUpRight aria-hidden="true" className="h-3 w-3" />
          </a>
          <a
            className="inline-flex items-center gap-1 transition-colors hover:text-ink"
            href={SITE_REPO}
            target="_blank"
            rel="noreferrer"
          >
            Source
            <ArrowUpRight aria-hidden="true" className="h-3 w-3" />
          </a>
        </div>
      </div>
    </footer>
  );
}
