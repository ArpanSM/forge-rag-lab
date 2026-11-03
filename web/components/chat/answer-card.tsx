import {
  AlertTriangle,
  ChevronRight,
  Clock,
  FileText,
  Fingerprint,
  ShieldCheck,
} from "lucide-react";
import type { Citation, Pipeline, QueryResponse, TenantId } from "@/lib/types";
import { cn } from "@/lib/utils";

interface AnswerCardProps {
  response: QueryResponse;
  tenant: TenantId;
  pipeline: Pipeline;
  onOpenCitation: (citation: Citation, tenant: TenantId) => void;
}

function PipelineBadge({ pipeline }: { pipeline: Pipeline }) {
  const fixed = pipeline === "fixed";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[0.68rem] font-semibold",
        fixed ? "bg-moss-soft text-moss" : "bg-amber-soft text-amber",
      )}
    >
      <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-current" />
      {fixed ? "Fixed pipeline" : "Baseline pipeline"}
    </span>
  );
}

function citationCount(response: QueryResponse): number {
  return response.claims.reduce((total, claim) => total + claim.citations.length, 0);
}

export function AnswerCard({ response, tenant, pipeline, onOpenCitation }: AnswerCardProps) {
  const totalCitations = citationCount(response);
  const hasUncitedClaims = !response.abstained && response.claims.length > 0 && totalCitations === 0;

  return (
    <article className="surface overflow-hidden">
      <header className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-line/80 px-5 py-3.5 sm:px-6">
        <PipelineBadge pipeline={pipeline} />
        <span className="font-mono text-[0.64rem] uppercase tracking-[0.14em] text-muted">
          {tenant}
        </span>
        <span className="ml-auto flex items-center gap-3 text-[0.68rem] text-muted">
          <span className="inline-flex items-center gap-1">
            <Clock aria-hidden="true" className="h-3 w-3" />
            {new Intl.NumberFormat("en").format(response.latency_ms)} ms
          </span>
          <span className="hidden items-center gap-1 sm:inline-flex">
            <Fingerprint aria-hidden="true" className="h-3 w-3" />
            <span title={response.trace_id}>{response.trace_id.slice(0, 10)}</span>
          </span>
        </span>
      </header>

      <div className="px-5 py-5 sm:px-6 sm:py-6">
        {response.abstained ? (
          <div className="rounded-2xl border border-amber/25 bg-amber-soft/55 p-4 sm:p-5">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface text-amber shadow-sm">
                <ShieldCheck aria-hidden="true" className="h-4 w-4" />
              </span>
              <div>
                <p className="font-semibold text-ink">Answer withheld — evidence is insufficient</p>
                <p className="mt-1 text-sm leading-6 text-amber">
                  The fixed pipeline abstains when the corpus has no block that supports an
                  answer. This is a deliberate outcome, not a retrieval crash.
                </p>
              </div>
            </div>
            <p className="mt-4 border-t border-amber/15 pt-3 text-sm leading-6 text-ink-soft">
              {response.answer}
            </p>
          </div>
        ) : (
          <>
            <p className="prose-answer whitespace-pre-line">{response.answer}</p>
            {hasUncitedClaims ? (
              <p className="mt-4 inline-flex items-center gap-2 rounded-full bg-danger-soft px-3 py-1.5 text-xs font-medium text-danger">
                <AlertTriangle aria-hidden="true" className="h-3.5 w-3.5" />
                This answer has claims but no supporting citations.
              </p>
            ) : null}
          </>
        )}

        {response.claims.length > 0 ? (
          <section className="mt-5 rounded-2xl border border-line bg-paper/55 p-3 sm:p-4">
            <div className="flex flex-wrap items-center justify-between gap-2 px-1">
              <h3 className="eyebrow">Claim support</h3>
              <span className="text-[0.68rem] text-muted">
                {response.claims.length} {response.claims.length === 1 ? "claim" : "claims"} ·{" "}
                {totalCitations} {totalCitations === 1 ? "citation" : "citations"}
              </span>
            </div>

            <ol className="mt-3 space-y-2.5">
              {response.claims.map((claim, index) => (
                <li
                  key={claim.claim_id}
                  className="rounded-xl border border-line/90 bg-surface px-3.5 py-3"
                >
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-ink font-mono text-[0.6rem] text-surface">
                      {index + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm leading-6 text-ink-soft">{claim.text}</p>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {claim.citations.length === 0 ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-danger-soft px-2.5 py-1 text-[0.66rem] font-medium text-danger">
                            <AlertTriangle aria-hidden="true" className="h-3 w-3" />
                            No citation
                          </span>
                        ) : (
                          claim.citations.map((citation) => (
                            <button
                              key={`${citation.doc_id}-${citation.version}-${citation.block_id}`}
                              type="button"
                              onClick={() => onOpenCitation(citation, tenant)}
                              aria-label={`Open citation: ${citation.title}, ${citation.version}, page ${citation.page}, block ${citation.block_id}`}
                              className="group inline-flex max-w-full items-center gap-1.5 rounded-full border border-line bg-paper/70 py-1 pl-2.5 pr-1.5 text-[0.68rem] text-ink-soft transition-colors hover:border-ember/40 hover:bg-ember-soft/50 hover:text-ink"
                            >
                              <FileText
                                aria-hidden="true"
                                className="h-3 w-3 shrink-0 text-ember"
                              />
                              <span className="truncate font-medium">{citation.title}</span>
                              <span className="shrink-0 font-mono text-[0.6rem] text-muted">
                                {citation.version} · p.{citation.page} · {citation.block_id}
                              </span>
                              <ChevronRight
                                aria-hidden="true"
                                className="h-3 w-3 shrink-0 text-muted transition-transform group-hover:translate-x-0.5"
                              />
                            </button>
                          ))
                        )}
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          </section>
        ) : null}
      </div>

      <footer className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-line/70 bg-paper/40 px-5 py-3 font-mono text-[0.6rem] uppercase tracking-[0.1em] text-muted sm:px-6">
        <span>model · {response.model}</span>
        <span className="hidden sm:inline">trace · {response.trace_id}</span>
        <span className="ml-auto">{pipeline === "fixed" ? "verified path" : "comparison path"}</span>
      </footer>
    </article>
  );
}
