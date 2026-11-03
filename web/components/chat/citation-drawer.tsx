"use client";

import { BookOpen, FileText, Hash, Quote, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { API_MODE, errorMessage, fetchDocBlock } from "@/lib/api";
import type { Citation, DocBlock, TenantId } from "@/lib/types";
import { cn } from "@/lib/utils";

interface CitationDrawerProps {
  citation: Citation | null;
  tenant: TenantId;
  onClose: () => void;
}

interface Range {
  start: number;
  end: number;
}

function findRanges(text: string, quote: string): Range[] {
  const lowerText = text.toLowerCase();
  const whole = quote.trim();
  const wholeIndex = whole ? lowerText.indexOf(whole.toLowerCase()) : -1;
  if (wholeIndex >= 0) {
    return [{ start: wholeIndex, end: wholeIndex + whole.length }];
  }

  const parts = quote
    .split(/…|\.\.\./)
    .map((part) => part.trim())
    .filter((part) => part.length >= 4);

  const ranges: Range[] = [];
  let cursor = 0;
  for (const part of parts) {
    const index = lowerText.indexOf(part.toLowerCase(), cursor);
    if (index >= 0) {
      ranges.push({ start: index, end: index + part.length });
      cursor = index + part.length;
    }
  }
  return ranges;
}

function HighlightedText({ text, quote }: { text: string; quote: string }) {
  const ranges = findRanges(text, quote);
  if (ranges.length === 0) return <>{text}</>;

  const nodes: ReactNode[] = [];
  let cursor = 0;
  ranges.forEach((range, index) => {
    if (range.start > cursor) {
      nodes.push(text.slice(cursor, range.start));
    }
    nodes.push(
      <mark key={`mark-${index}`} className="citation-mark">
        {text.slice(range.start, range.end)}
      </mark>,
    );
    cursor = range.end;
  });
  if (cursor < text.length) nodes.push(text.slice(cursor));
  return <>{nodes}</>;
}

function MetaItem({
  label,
  value,
  mono = false,
  wide = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
  wide?: boolean;
}) {
  return (
    <div className={cn("rounded-xl border border-line/80 bg-paper/45 px-3 py-2.5", wide && "col-span-2")}>
      <dt className="eyebrow text-[0.6rem]">{label}</dt>
      <dd className={cn("mt-1 truncate text-sm text-ink-soft", mono && "font-mono text-xs")}>
        {value}
      </dd>
    </div>
  );
}

export function CitationDrawer({ citation, tenant, onClose }: CitationDrawerProps) {
  const [block, setBlock] = useState<DocBlock | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const panelRef = useRef<HTMLElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!citation) return;
    const controller = new AbortController();
    setBlock(null);
    setError(null);
    setLoading(true);

    fetchDocBlock(
      tenant,
      citation.doc_id,
      citation.block_id,
      citation.version,
      controller.signal,
    )
      .then((result) => {
        setBlock(result);
      })
      .catch((fetchError: unknown) => {
        if (fetchError instanceof DOMException && fetchError.name === "AbortError") return;
        setError(errorMessage(fetchError));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [citation, tenant]);

  useEffect(() => {
    if (!citation) return;

    const previousFocus = document.activeElement as HTMLElement | null;
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const focusTimer = window.requestAnimationFrame(() => {
      closeRef.current?.focus();
    });

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab") return;

      const focusable = panelRef.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), a[href], input, textarea, select, [tabindex]:not([tabindex="-1"])',
      );
      if (!focusable || focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = originalOverflow;
      window.cancelAnimationFrame(focusTimer);
      previousFocus?.focus();
    };
  }, [citation, onClose]);

  if (!citation) return null;

  const title = block?.title ?? citation.title;
  const version = block?.version ?? citation.version;
  const page = block?.page ?? citation.page;
  const blockId = block?.block_id ?? citation.block_id;
  const anchor = block?.anchor ?? citation.anchor;
  const body = block?.text ?? citation.quote;
  const heading = block?.heading ?? "Cited block";
  const highlightFound = findRanges(body, citation.quote).length > 0;

  return (
    <div className="fixed inset-0 z-50">
      <button
        type="button"
        aria-label="Close citation viewer"
        tabIndex={-1}
        onClick={onClose}
        className="animate-fade absolute inset-0 h-full w-full cursor-default bg-ink/45 backdrop-blur-[2px]"
      />

      <aside
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="citation-drawer-title"
        className="animate-drawer absolute inset-y-0 right-0 flex w-full max-w-xl flex-col border-l border-line bg-surface shadow-lift"
      >
        <header className="border-b border-line bg-paper/55 px-5 py-5 sm:px-7">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="eyebrow">Citation viewer · {tenant}</p>
              <h2
                id="citation-drawer-title"
                className="mt-1.5 truncate font-display text-2xl tracking-[-0.015em] text-ink"
              >
                {title}
              </h2>
              <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                <span className="rounded-full bg-ink px-2.5 py-1 font-mono text-[0.62rem] uppercase tracking-[0.12em] text-surface">
                  {version}
                </span>
                <span className="rounded-full border border-line bg-surface px-2.5 py-1 font-mono text-[0.62rem] uppercase tracking-[0.12em] text-muted">
                  page {page}
                </span>
                <span className="rounded-full border border-line bg-surface px-2.5 py-1 font-mono text-[0.62rem] uppercase tracking-[0.12em] text-muted">
                  block {blockId}
                </span>
              </div>
            </div>
            <button
              ref={closeRef}
              type="button"
              onClick={onClose}
              aria-label="Close citation viewer"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-line bg-surface text-muted transition-colors hover:border-line-strong hover:text-ink"
            >
              <X aria-hidden="true" className="h-4 w-4" />
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-6 sm:px-7">
          <dl className="grid grid-cols-2 gap-2">
            <MetaItem label="Document" value={title} wide />
            <MetaItem label="Version" value={version} mono />
            <MetaItem label="Page" value={String(page)} mono />
            <MetaItem label="Block" value={blockId} mono />
            <MetaItem label="Tenant" value={tenant} mono />
            <MetaItem label="Anchor" value={anchor} mono wide />
          </dl>

          <div className="mt-5 overflow-hidden rounded-2xl border border-line bg-surface-strong">
            <div className="flex items-center gap-2 border-b border-line bg-paper/55 px-4 py-3">
              <BookOpen aria-hidden="true" className="h-3.5 w-3.5 text-ember" />
              <span className="eyebrow text-[0.62rem]">Source block · {blockId}</span>
              <span className="ml-auto inline-flex items-center gap-1 font-mono text-[0.62rem] text-muted">
                <Hash aria-hidden="true" className="h-3 w-3" />
                {anchor.replace(/^#/, "")}
              </span>
            </div>

            {loading ? (
              <div className="space-y-3 p-5" aria-label="Loading cited block">
                <div className="skeleton h-4 w-2/3 rounded" />
                <div className="skeleton h-3 w-full rounded" />
                <div className="skeleton h-3 w-full rounded" />
                <div className="skeleton h-3 w-4/5 rounded" />
              </div>
            ) : (
              <div className="p-5">
                <h3 className="font-display text-xl tracking-[-0.01em] text-ink">{heading}</h3>
                <p className="mt-3 text-[0.94rem] leading-7 text-ink-soft">
                  <HighlightedText text={body} quote={citation.quote} />
                </p>
                <p className="mt-4 flex items-center gap-1.5 text-[0.66rem] text-muted">
                  <Quote aria-hidden="true" className="h-3 w-3 text-ember" />
                  {highlightFound
                    ? "The highlighted span is the quote returned with the answer."
                    : "The block text is shown; the exact quote is listed below."}
                </p>
              </div>
            )}
          </div>

          {error ? (
            <div className="mt-4 rounded-xl border border-danger/20 bg-danger-soft/60 px-4 py-3 text-xs leading-5 text-danger">
              <p className="font-medium">Could not fetch the live block.</p>
              <p className="mt-0.5">{error} Showing the citation payload instead.</p>
            </div>
          ) : null}

          <div className="mt-4 rounded-2xl border-l-2 border-ember bg-ember-soft/35 px-4 py-4">
            <p className="eyebrow text-[0.6rem]">Cited quote</p>
            <p className="mt-1.5 text-sm leading-6 text-ink-soft">“{citation.quote}”</p>
          </div>

          <div className="mt-4 flex items-start gap-2 rounded-xl border border-line/80 bg-paper/45 px-3.5 py-3 text-[0.68rem] leading-5 text-muted">
            <FileText aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ember" />
            <span>
              Citation reads are tenant-scoped. The drawer resolves the exact document version,
              page, block and anchor before it shows the quote.
            </span>
          </div>
        </div>

        <footer className="border-t border-line bg-paper/50 px-5 py-3.5 sm:px-7">
          <p className="truncate font-mono text-[0.62rem] text-muted">
            GET /api/docs/{citation.doc_id}/blocks/{citation.block_id}?tenant_id={tenant}
            {citation.version ? `&version=${citation.version}` : ""}
          </p>
          <p className="mt-1 text-[0.64rem] text-muted">
            {API_MODE === "mock" ? "Served from bundled fixtures." : "Served by the live API."} Press{" "}
            <kbd className="rounded border border-line bg-surface px-1 py-0.5 font-mono text-[0.62rem]">
              Esc
            </kbd>{" "}
            to close.
          </p>
        </footer>
      </aside>
    </div>
  );
}
