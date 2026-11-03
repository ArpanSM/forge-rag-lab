"use client";

import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  CalendarDays,
  CheckCircle2,
  FileText,
  Info,
  Minus,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { errorMessage, fetchEvalSummary, fetchFailures } from "@/lib/api";
import { categoryLabel, failureMeta } from "@/lib/failure-meta";
import {
  METRIC_GROUPS,
  type MetricGroup,
  deltaTone,
  formatDelta,
  formatMetric,
  metricBarWidth,
  metricMeta,
} from "@/lib/metric-meta";
import type { Citation, EvalMetricRow, EvalSummary, FailureCase } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

function DeltaBadge({ row }: { row: EvalMetricRow }) {
  const meta = metricMeta(row.metric);
  const tone = deltaTone(row, meta);
  const Icon = row.delta > 0 ? ArrowUpRight : row.delta < 0 ? ArrowDownRight : Minus;

  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center gap-0.5 rounded-full px-2 py-1 font-mono text-[0.6rem] font-medium",
        tone === "good"
          ? "bg-moss-soft text-moss"
          : tone === "bad"
            ? "bg-danger-soft text-danger"
            : "bg-paper text-muted",
      )}
    >
      <Icon aria-hidden="true" className="h-3 w-3" />
      {formatDelta(row, meta.unit)}
    </span>
  );
}

function SummaryTile({ row, label }: { row: EvalMetricRow; label: string }) {
  const meta = metricMeta(row.metric);
  const tone = deltaTone(row, meta);
  return (
    <div className="surface p-4 sm:p-5">
      <div className="flex min-h-8 items-start justify-between gap-2">
        <p className="eyebrow">{label}</p>
        <DeltaBadge row={row} />
      </div>
      <p className="mt-3 font-display text-[2rem] leading-none tracking-[-0.02em] text-ink sm:text-[2.4rem]">
        {formatMetric(row.fixed, meta.unit)}
      </p>
      <p className="mt-1.5 text-[0.64rem] text-muted">
        baseline {formatMetric(row.baseline, meta.unit)} · n={row.n}
      </p>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-paper">
        <div
          className={cn("h-full rounded-full", tone === "bad" ? "bg-ember" : "bg-moss")}
          style={{ width: `${metricBarWidth(row.fixed, meta.unit)}%` }}
        />
      </div>
    </div>
  );
}

function CitationChips({
  citations,
  emptyLabel = "no citation",
}: {
  citations: Citation[];
  emptyLabel?: string;
}) {
  if (citations.length === 0) {
    return (
      <p className="mt-2 inline-flex items-center gap-1 rounded-full bg-paper px-2 py-1 font-mono text-[0.6rem] uppercase tracking-[0.08em] text-muted">
        {emptyLabel}
      </p>
    );
  }
  return (
    <div className="mt-2 flex flex-wrap gap-1">
      {citations.map((citation) => (
        <span
          key={`${citation.doc_id}-${citation.version}-${citation.block_id}`}
          className="inline-flex max-w-full items-center gap-1 rounded-full border border-line/80 bg-surface/70 px-2 py-0.5 font-mono text-[0.6rem] text-muted"
        >
          <FileText aria-hidden="true" className="h-2.5 w-2.5 shrink-0 text-ember" />
          <span className="truncate">{citation.title}</span>
          <span className="shrink-0">
            {citation.version} · p.{citation.page} · {citation.block_id}
          </span>
        </span>
      ))}
    </div>
  );
}

function FailureCard({ failure }: { failure: FailureCase }) {
  const meta = failureMeta(failure.failure);
  return (
    <article className="surface flex h-full flex-col overflow-hidden">
      <header className="border-b border-line/80 px-5 py-4">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-mono text-[0.6rem] uppercase tracking-[0.1em]",
              meta.severity === "high"
                ? "bg-danger-soft text-danger"
                : meta.severity === "medium"
                  ? "bg-amber-soft text-amber"
                  : "bg-paper text-muted",
            )}
          >
            {meta.severity}
          </span>
          <span className="text-[0.68rem] font-semibold text-ink">{meta.label}</span>
          <span className="ml-auto font-mono text-[0.6rem] uppercase tracking-[0.1em] text-muted">
            {categoryLabel(failure.category)} · {failure.question_id}
          </span>
        </div>
        <h3 className="mt-2.5 text-sm font-semibold leading-6 text-ink">{failure.question}</h3>
      </header>

      <div className="flex-1 space-y-2.5 px-5 py-4">
        <div className="rounded-xl border border-danger/15 bg-danger-soft/35 p-3">
          <p className="inline-flex items-center gap-1.5 font-mono text-[0.6rem] uppercase tracking-[0.12em] text-danger">
            <span aria-hidden="true" className="h-1 w-1 rounded-full bg-danger" />
            Baseline
          </p>
          <p className="mt-1.5 text-[0.72rem] leading-5 text-ink-soft">{failure.baseline_answer}</p>
          <CitationChips citations={failure.baseline_citations ?? []} />
        </div>

        <div className="rounded-xl border border-moss/15 bg-moss-soft/35 p-3">
          <p className="inline-flex items-center gap-1.5 font-mono text-[0.6rem] uppercase tracking-[0.12em] text-moss">
            <span aria-hidden="true" className="h-1 w-1 rounded-full bg-moss" />
            Fixed
          </p>
          <p className="mt-1.5 text-[0.72rem] leading-5 text-ink-soft">{failure.fixed_answer}</p>
          <CitationChips citations={failure.fixed_citations ?? []} emptyLabel="abstained" />
        </div>

        <p className="flex items-start gap-1.5 text-[0.66rem] leading-5 text-muted">
          <Info aria-hidden="true" className="mt-0.5 h-3 w-3 shrink-0 text-ember" />
          <span>{failure.explanation ?? meta.explanation}</span>
        </p>
      </div>
    </article>
  );
}

function LoadingReport() {
  return (
    <div className="mt-8 space-y-8" aria-label="Loading evaluation report">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {[0, 1, 2, 3].map((item) => (
          <div key={item} className="skeleton h-40 rounded-3xl" />
        ))}
      </div>
      <div className="skeleton h-[26rem] rounded-3xl" />
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="skeleton h-72 rounded-3xl" />
        <div className="skeleton h-72 rounded-3xl" />
      </div>
    </div>
  );
}

export function HealthReport() {
  const [summary, setSummary] = useState<EvalSummary | null>(null);
  const [failures, setFailures] = useState<FailureCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metricGroup, setMetricGroup] = useState<MetricGroup | "all">("all");
  const [failureFilter, setFailureFilter] = useState<string>("all");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    Promise.all([fetchEvalSummary(controller.signal), fetchFailures(controller.signal)])
      .then(([nextSummary, nextFailures]) => {
        setSummary(nextSummary);
        setFailures(nextFailures);
      })
      .catch((fetchError: unknown) => {
        if (fetchError instanceof DOMException && fetchError.name === "AbortError") return;
        setError(errorMessage(fetchError));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [reloadKey]);

  const summaryRows = summary?.rows ?? [];
  const groupedRows = useMemo(
    () =>
      METRIC_GROUPS.map((group) => ({
        ...group,
        rows: summaryRows.filter((row) => metricMeta(row.metric).group === group.id),
      })).filter(
        (group) =>
          group.rows.length > 0 && (metricGroup === "all" || group.id === metricGroup),
      ),
    [metricGroup, summaryRows],
  );

  const failureTypes = useMemo(
    () => Array.from(new Set(failures.map((failure) => failure.failure))),
    [failures],
  );
  const filteredFailures = useMemo(
    () =>
      failureFilter === "all"
        ? failures
        : failures.filter((failure) => failure.failure === failureFilter),
    [failureFilter, failures],
  );

  const citationRow = summaryRows.find((row) => row.metric === "citation_page_accuracy");
  const staleRow = summaryRows.find((row) => row.metric === "stale_citation_rate");
  const abstentionRow = summaryRows.find((row) => row.metric === "abstention_accuracy");
  const latencyRow = summaryRows.find((row) => row.metric === "p95_latency_ms");
  const sampleSize = summaryRows[0]?.n;

  if (loading) return <LoadingReport />;

  if (error || !summary) {
    return (
      <div className="mt-8 rounded-3xl border border-danger/25 bg-danger-soft/45 p-6 sm:p-8">
        <div className="flex items-start gap-3">
          <AlertTriangle aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-danger" />
          <div>
            <p className="font-semibold text-danger">The evaluation report could not load.</p>
            <p className="mt-1 text-sm leading-6 text-ink-soft">
              {error ?? "The API returned an empty summary."}
            </p>
            <button
              type="button"
              onClick={() => setReloadKey((key) => key + 1)}
              className="mt-4 inline-flex items-center gap-2 rounded-full bg-ink px-4 py-2 text-xs font-semibold text-surface transition-colors hover:bg-ink-soft"
            >
              <RefreshCw aria-hidden="true" className="h-3.5 w-3.5" />
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="font-display text-2xl tracking-[-0.02em] text-ink sm:text-3xl">
            Baseline vs fixed
          </h2>
          <p className="mt-1 text-sm leading-6 text-muted">
            Same questions, same judge, same test split. The delta is fixed minus baseline.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface/70 px-3 py-1.5 text-[0.64rem] text-muted">
            <CalendarDays aria-hidden="true" className="h-3 w-3" />
            {formatDate(summary.generated_at)}
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface/70 px-3 py-1.5 text-[0.64rem] text-muted">
            <CheckCircle2 aria-hidden="true" className="h-3 w-3 text-moss" />
            n={sampleSize ?? 80}
          </span>
          {summary.note ? (
            <span className="hidden rounded-full border border-line bg-surface/70 px-3 py-1.5 font-mono text-[0.6rem] text-muted xl:inline-flex">
              {summary.note}
            </span>
          ) : null}
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {citationRow ? (
          <SummaryTile row={citationRow} label="Citation page accuracy" />
        ) : null}
        {staleRow ? <SummaryTile row={staleRow} label="Stale citation rate" /> : null}
        {abstentionRow ? (
          <SummaryTile row={abstentionRow} label="Abstention accuracy" />
        ) : null}
        {latencyRow ? <SummaryTile row={latencyRow} label="p95 latency" /> : null}
      </div>

      <section className="mt-10" aria-labelledby="metric-table-heading">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="eyebrow">Metric table</p>
            <h2
              id="metric-table-heading"
              className="mt-1 font-display text-2xl tracking-[-0.02em] text-ink"
            >
              Where the fixed pipeline earns its keep
            </h2>
          </div>
          <p className="max-w-sm text-xs leading-5 text-muted">
            Green deltas are improvements. For rates marked lower-is-better and for latency, a
            negative delta is the good direction.
          </p>
        </div>

        <div className="mt-4 flex flex-wrap gap-1.5" role="group" aria-label="Filter metrics">
          <button
            type="button"
            aria-pressed={metricGroup === "all"}
            onClick={() => setMetricGroup("all")}
            className={cn(
              "rounded-full border px-3 py-1.5 text-[0.66rem] font-medium transition-colors",
              metricGroup === "all"
                ? "border-ink bg-ink text-surface"
                : "border-line bg-surface/60 text-muted hover:border-line-strong hover:text-ink",
            )}
          >
            All metrics
            <span className="ml-1.5 font-mono text-[0.6rem] opacity-60">{summaryRows.length}</span>
          </button>
          {METRIC_GROUPS.map((group) => {
            const count = summaryRows.filter((row) => metricMeta(row.metric).group === group.id)
              .length;
            if (count === 0) return null;
            return (
              <button
                key={group.id}
                type="button"
                aria-pressed={metricGroup === group.id}
                onClick={() => setMetricGroup(group.id)}
                className={cn(
                  "rounded-full border px-3 py-1.5 text-[0.66rem] font-medium transition-colors",
                  metricGroup === group.id
                    ? "border-ink bg-ink text-surface"
                    : "border-line bg-surface/60 text-muted hover:border-line-strong hover:text-ink",
                )}
              >
                {group.label}
                <span className="ml-1.5 font-mono text-[0.6rem] opacity-60">{count}</span>
              </button>
            );
          })}
        </div>

        <div className="mt-4 overflow-hidden rounded-3xl border border-line bg-surface shadow-card">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[48rem] text-left">
              <thead className="border-b border-line bg-paper/55">
                <tr>
                  <th scope="col" className="px-5 py-3.5">
                    <span className="eyebrow">Metric</span>
                  </th>
                  <th scope="col" className="w-[19%] px-5 py-3.5">
                    <span className="eyebrow">Baseline</span>
                  </th>
                  <th scope="col" className="w-[19%] px-5 py-3.5">
                    <span className="eyebrow">Fixed</span>
                  </th>
                  <th scope="col" className="w-[14%] px-5 py-3.5">
                    <span className="eyebrow">Delta</span>
                  </th>
                  <th scope="col" className="w-[7%] px-5 py-3.5 text-right">
                    <span className="eyebrow">n</span>
                  </th>
                </tr>
              </thead>
              {groupedRows.map((group) => (
                <tbody key={group.id} className="border-b border-line/70 last:border-b-0">
                  <tr className="bg-paper/35">
                    <th
                      colSpan={5}
                      scope="colgroup"
                      className="px-5 py-2.5 text-left font-normal"
                    >
                      <span className="text-[0.66rem] font-semibold text-ink">{group.label}</span>
                      <span className="ml-2 text-[0.62rem] text-muted">{group.description}</span>
                    </th>
                  </tr>
                  {group.rows.map((row) => {
                    const meta = metricMeta(row.metric);
                    return (
                      <tr
                        key={row.metric}
                        className="border-t border-line/60 transition-colors hover:bg-paper/30"
                      >
                        <td className="px-5 py-4">
                          <p className="text-sm font-medium text-ink">
                            {meta.label}
                            {meta.lowerIsBetter ? (
                              <span className="ml-1.5 align-middle font-mono text-[0.6rem] font-normal text-moss">
                                ↓ better
                              </span>
                            ) : null}
                          </p>
                          <p className="mt-0.5 max-w-md text-[0.66rem] leading-5 text-muted">
                            {meta.description}
                          </p>
                        </td>
                        <td className="px-5 py-4">
                          <p className="font-mono text-[0.78rem] text-muted">
                            {formatMetric(row.baseline, meta.unit)}
                          </p>
                          <div className="mt-1.5 h-1 w-full max-w-[6rem] overflow-hidden rounded-full bg-paper">
                            <div
                              className="h-full rounded-full bg-line-strong"
                              style={{ width: `${metricBarWidth(row.baseline, meta.unit)}%` }}
                            />
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <p className="font-mono text-[0.78rem] font-semibold text-ink">
                            {formatMetric(row.fixed, meta.unit)}
                          </p>
                          <div className="mt-1.5 h-1 w-full max-w-[6rem] overflow-hidden rounded-full bg-paper">
                            <div
                              className="h-full rounded-full bg-moss"
                              style={{ width: `${metricBarWidth(row.fixed, meta.unit)}%` }}
                            />
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <DeltaBadge row={row} />
                        </td>
                        <td className="px-5 py-4 text-right font-mono text-[0.72rem] text-muted">
                          {row.n}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              ))}
            </table>
          </div>
          <div className="border-t border-line bg-paper/45 px-5 py-3 text-[0.64rem] leading-5 text-muted">
            {summary.note ?? "Proportions are shown as percentages."} Lower is better for stale
            rates, false abstentions and latency.
          </div>
        </div>
      </section>

      <section className="mt-12" aria-labelledby="failure-gallery-heading">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="eyebrow">Failure gallery</p>
            <h2
              id="failure-gallery-heading"
              className="mt-1 font-display text-2xl tracking-[-0.02em] text-ink"
            >
              Seven ways retrieval goes wrong
            </h2>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-muted">
              Short, inspectable examples from the evaluation set. Each card shows the baseline
              answer, the fixed answer and the mechanism behind the failure.
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 self-start rounded-full border border-line bg-surface/70 px-3 py-1.5 text-[0.64rem] text-muted sm:self-auto">
            <ShieldAlert aria-hidden="true" className="h-3 w-3 text-ember" />
            {filteredFailures.length} of {failures.length} examples
          </span>
        </div>

        <div className="mt-4 flex flex-wrap gap-1.5" role="group" aria-label="Filter failures">
          <button
            type="button"
            aria-pressed={failureFilter === "all"}
            onClick={() => setFailureFilter("all")}
            className={cn(
              "rounded-full border px-3 py-1.5 text-[0.66rem] font-medium transition-colors",
              failureFilter === "all"
                ? "border-ink bg-ink text-surface"
                : "border-line bg-surface/60 text-muted hover:border-line-strong hover:text-ink",
            )}
          >
            All failures
          </button>
          {failureTypes.map((code) => (
            <button
              key={code}
              type="button"
              aria-pressed={failureFilter === code}
              onClick={() => setFailureFilter(code)}
              className={cn(
                "rounded-full border px-3 py-1.5 text-[0.66rem] font-medium transition-colors",
                failureFilter === code
                  ? "border-ink bg-ink text-surface"
                  : "border-line bg-surface/60 text-muted hover:border-line-strong hover:text-ink",
              )}
            >
              {failureMeta(code).label}
            </button>
          ))}
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          {filteredFailures.map((failure) => (
            <FailureCard key={failure.question_id} failure={failure} />
          ))}
        </div>
      </section>
    </div>
  );
}
