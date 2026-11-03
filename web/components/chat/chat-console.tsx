"use client";

import {
  ArrowRight,
  ArrowUp,
  Check,
  Database,
  FileSearch,
  GitCompare,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent as ReactKeyboardEvent, ReactNode } from "react";
import { API_BASE_URL, API_MODE, askQuestion, errorMessage, fetchDemoQuestions } from "@/lib/api";
import { categoryLabel } from "@/lib/failure-meta";
import type { Citation, DemoQuestion, Pipeline, QueryResponse, TenantId } from "@/lib/types";
import { cn, formatTrace } from "@/lib/utils";
import { AnswerCard } from "./answer-card";
import { CitationDrawer } from "./citation-drawer";

interface Turn {
  id: string;
  question: string;
  tenant: TenantId;
  pipeline: Pipeline;
  response: QueryResponse;
}

interface ActiveCitation {
  citation: Citation;
  tenant: TenantId;
}

const TENANTS: Array<{ id: TenantId; label: string; detail: string }> = [
  { id: "northwind", label: "Northwind", detail: "Primary workspace" },
  { id: "acme", label: "Acme", detail: "Isolated tenant" },
];

const PIPELINES: Array<{
  id: Pipeline;
  label: string;
  detail: string;
}> = [
  {
    id: "fixed",
    label: "Fixed",
    detail: "Hybrid retrieval · version filters · reranker · abstains",
  },
  {
    id: "baseline",
    label: "Baseline",
    detail: "Dense-only · fixed chunks · no filters · always answers",
  },
];

function newTurnId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `turn-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function ModeNote() {
  const live = API_MODE === "live";
  return (
    <div className="rounded-2xl border border-line/80 bg-paper/55 px-3 py-3">
      <div className="flex items-center gap-1.5">
        <span
          aria-hidden="true"
          className={cn("h-1.5 w-1.5 rounded-full", live ? "bg-moss" : "bg-ember")}
        />
        <span className="font-mono text-[0.62rem] uppercase tracking-[0.14em] text-muted">
          {live ? "Live API" : "Mock fixtures"}
        </span>
      </div>
      <p className="mt-1.5 text-[0.66rem] leading-5 text-muted">
        {live
          ? `Queries are sent to ${API_BASE_URL}.`
          : "The UI runs without the backend. Set NEXT_PUBLIC_API_BASE at build time to switch."}
      </p>
    </div>
  );
}

function ControlCard({ children }: { children: ReactNode }) {
  return <section className="surface p-4 sm:p-5">{children}</section>;
}

export function ChatConsole() {
  const [tenant, setTenant] = useState<TenantId>("northwind");
  const [pipeline, setPipeline] = useState<Pipeline>("fixed");
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRun, setLastRun] = useState<{ question: string; tenant: TenantId } | null>(null);
  const [activeCitation, setActiveCitation] = useState<ActiveCitation | null>(null);
  const [demoQuestions, setDemoQuestions] = useState<DemoQuestion[]>([]);
  const [samplesLoading, setSamplesLoading] = useState(true);
  const [samplesError, setSamplesError] = useState<string | null>(null);

  const requestController = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchDemoQuestions(controller.signal)
      .then(setDemoQuestions)
      .catch((fetchError: unknown) => {
        if (fetchError instanceof DOMException && fetchError.name === "AbortError") return;
        setSamplesError(errorMessage(fetchError));
      })
      .finally(() => {
        if (!controller.signal.aborted) setSamplesLoading(false);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    return () => {
      requestController.current?.abort();
    };
  }, []);

  useEffect(() => {
    if (turns.length === 0) return;
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [turns.length]);

  const samples = useMemo(
    () => demoQuestions.filter((demo) => demo.tenant_id === tenant),
    [demoQuestions, tenant],
  );

  const runQuestion = useCallback(
    async (rawQuestion: string, selectedTenant: TenantId, selectedPipeline: Pipeline, clearInput = true) => {
      const trimmed = rawQuestion.trim();
      if (!trimmed) return;

      requestController.current?.abort();
      const controller = new AbortController();
      requestController.current = controller;
      setIsLoading(true);
      setError(null);
      setLastRun({ question: trimmed, tenant: selectedTenant });

      try {
        const response = await askQuestion(
          {
            tenant_id: selectedTenant,
            question: trimmed,
            pipeline: selectedPipeline,
          },
          controller.signal,
        );
        setTurns((current) => [
          ...current,
          {
            id: newTurnId(),
            question: trimmed,
            tenant: selectedTenant,
            pipeline: selectedPipeline,
            response,
          },
        ]);
        if (clearInput) {
          setQuestion((current) => (current === rawQuestion ? "" : current));
        }
      } catch (requestError: unknown) {
        if (controller.signal.aborted) return;
        setError(errorMessage(requestError));
      } finally {
        if (requestController.current === controller) {
          requestController.current = null;
          setIsLoading(false);
        }
      }
    },
    [],
  );

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isLoading) return;
    void runQuestion(question, tenant, pipeline);
  }

  function handleTextareaKeyDown(event: ReactKeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      if (!isLoading && question.trim()) {
        void runQuestion(question, tenant, pipeline);
      }
    }
  }

  function handleTenantChange(nextTenant: TenantId) {
    if (isLoading || nextTenant === tenant) return;
    setTenant(nextTenant);
    setLastRun(null);
    setError(null);
  }

  function handlePipelineChange(nextPipeline: Pipeline) {
    if (isLoading || nextPipeline === pipeline) return;
    setPipeline(nextPipeline);
    if (lastRun && lastRun.tenant === tenant) {
      void runQuestion(lastRun.question, tenant, nextPipeline, false);
    }
  }

  function handleSample(demo: DemoQuestion) {
    if (isLoading) return;
    setQuestion(demo.question);
    void runQuestion(demo.question, demo.tenant_id, pipeline, true);
  }

  const closeDrawer = useCallback(() => setActiveCitation(null), []);
  const canCompare = Boolean(lastRun && lastRun.tenant === tenant);

  return (
    <>
      <div className="grid gap-5 lg:grid-cols-[19rem_minmax(0,1fr)] lg:items-start lg:gap-6">
        <aside className="space-y-4 lg:sticky lg:top-24">
          <ControlCard>
            <div className="flex items-center justify-between gap-3">
              <h2 className="eyebrow">Workspace</h2>
              <Database aria-hidden="true" className="h-3.5 w-3.5 text-muted" />
            </div>
            <div className="mt-3 grid grid-cols-2 gap-1 rounded-2xl border border-line bg-paper/60 p-1">
              {TENANTS.map((item) => {
                const selected = tenant === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    aria-pressed={selected}
                    onClick={() => handleTenantChange(item.id)}
                    disabled={isLoading}
                    className={cn(
                      "rounded-xl px-2.5 py-2 text-left transition-all disabled:cursor-not-allowed disabled:opacity-60",
                      selected
                        ? "bg-surface-strong shadow-sm ring-1 ring-line"
                        : "text-muted hover:bg-surface/60 hover:text-ink",
                    )}
                  >
                    <span className="flex items-center gap-1.5 text-[0.78rem] font-semibold">
                      <span
                        aria-hidden="true"
                        className={cn(
                          "h-1.5 w-1.5 rounded-full",
                          selected ? "bg-ember" : "bg-line-strong",
                        )}
                      />
                      {item.label}
                    </span>
                    <span className="mt-0.5 block text-[0.62rem] text-muted">{item.detail}</span>
                  </button>
                );
              })}
            </div>
            <p className="mt-3 text-[0.66rem] leading-5 text-muted">
              Tenant filters apply to retrieval and every citation read. Acme keeps its own private
              runbook.
            </p>
          </ControlCard>

          <ControlCard>
            <div className="flex items-center justify-between gap-3">
              <h2 className="eyebrow">Pipeline</h2>
              <GitCompare aria-hidden="true" className="h-3.5 w-3.5 text-muted" />
            </div>
            <div className="mt-3 space-y-2">
              {PIPELINES.map((item) => {
                const selected = pipeline === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    aria-pressed={selected}
                    onClick={() => handlePipelineChange(item.id)}
                    disabled={isLoading}
                    className={cn(
                      "w-full rounded-2xl border p-3 text-left transition-all disabled:cursor-not-allowed disabled:opacity-60",
                      selected
                        ? item.id === "fixed"
                          ? "border-moss/30 bg-moss-soft/55"
                          : "border-amber/30 bg-amber-soft/55"
                        : "border-line bg-surface/60 hover:border-line-strong hover:bg-surface",
                    )}
                  >
                    <span className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-2 text-[0.8rem] font-semibold text-ink">
                        <span
                          aria-hidden="true"
                          className={cn(
                            "flex h-4 w-4 items-center justify-center rounded-full border",
                            selected
                              ? item.id === "fixed"
                                ? "border-moss bg-moss text-surface"
                                : "border-amber bg-amber text-surface"
                              : "border-line-strong bg-surface",
                          )}
                        >
                          {selected ? <Check className="h-2.5 w-2.5" /> : null}
                        </span>
                        {item.label}
                      </span>
                      <span
                        className={cn(
                          "font-mono text-[0.6rem] uppercase tracking-[0.12em]",
                          item.id === "fixed" ? "text-moss" : "text-amber",
                        )}
                      >
                        {item.id === "fixed" ? "verified" : "compare"}
                      </span>
                    </span>
                    <span className="mt-1.5 block pl-6 text-[0.64rem] leading-5 text-muted">
                      {item.detail}
                    </span>
                  </button>
                );
              })}
            </div>
            <p className="mt-3 text-[0.66rem] leading-5 text-muted">
              {canCompare
                ? "Switching pipelines re-runs your last question for a direct comparison."
                : "Run a question, then switch pipelines to compare the same query."}
            </p>
          </ControlCard>

          <ControlCard>
            <div className="flex items-center justify-between gap-3">
              <h2 className="eyebrow">Try a question</h2>
              <Sparkles aria-hidden="true" className="h-3.5 w-3.5 text-ember" />
            </div>

            {samplesLoading ? (
              <div className="mt-3 space-y-2">
                {[0, 1, 2].map((item) => (
                  <div key={item} className="skeleton h-12 rounded-xl" />
                ))}
              </div>
            ) : samplesError ? (
              <p className="mt-3 rounded-xl bg-danger-soft/60 px-3 py-2 text-[0.66rem] leading-5 text-danger">
                Sample questions could not load. {samplesError}
              </p>
            ) : (
              <ul className="mt-2.5 space-y-1">
                {samples.map((demo) => (
                  <li key={demo.id}>
                    <button
                      type="button"
                      onClick={() => handleSample(demo)}
                      disabled={isLoading}
                      className="group flex w-full items-start gap-2 rounded-xl px-1.5 py-2 text-left transition-colors hover:bg-paper/70 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <ArrowRight
                        aria-hidden="true"
                        className="mt-1 h-3 w-3 shrink-0 text-line-strong transition-all group-hover:translate-x-0.5 group-hover:text-ember"
                      />
                      <span className="min-w-0">
                        <span className="line-clamp-2 block text-[0.72rem] font-medium leading-5 text-ink-soft group-hover:text-ink">
                          {demo.question}
                        </span>
                        <span className="mt-0.5 block font-mono text-[0.6rem] uppercase tracking-[0.1em] text-muted">
                          {categoryLabel(demo.category)}
                        </span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}

            <div className="mt-3">
              <ModeNote />
            </div>
          </ControlCard>
        </aside>

        <div className="min-w-0 space-y-5">
          <form onSubmit={handleSubmit} className="surface overflow-hidden">
            <div className="p-4 sm:p-5">
              <div className="flex items-center justify-between gap-3">
                <label htmlFor="question-input" className="eyebrow">
                  Ask Helios
                </label>
                <span className="font-mono text-[0.6rem] uppercase tracking-[0.12em] text-muted">
                  {tenant} · {pipeline}
                </span>
              </div>
              <textarea
                id="question-input"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={handleTextareaKeyDown}
                rows={2}
                placeholder="e.g. How do I rotate an API key in v3?"
                className="mt-2 min-h-[4.5rem] w-full resize-none border-0 bg-transparent p-0 text-[1rem] leading-7 text-ink placeholder:text-muted/65 focus:outline-none"
              />
              <div className="mt-2 flex flex-col gap-3 border-t border-line/70 pt-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-[0.66rem] text-muted">
                  <kbd className="rounded border border-line bg-paper px-1 py-0.5 font-mono text-[0.6rem]">
                    Enter
                  </kbd>{" "}
                  to send ·{" "}
                  <kbd className="rounded border border-line bg-paper px-1 py-0.5 font-mono text-[0.6rem]">
                    Shift + Enter
                  </kbd>{" "}
                  for a new line
                </p>
                <button
                  type="submit"
                  disabled={isLoading || question.trim().length === 0}
                  className="inline-flex items-center justify-center gap-2 rounded-full bg-ink px-5 py-2.5 text-[0.76rem] font-semibold text-surface transition-all hover:bg-ink-soft disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {isLoading ? "Running query" : "Run query"}
                  <ArrowUp aria-hidden="true" className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-line/60 bg-paper/45 px-5 py-2.5 font-mono text-[0.6rem] uppercase tracking-[0.12em] text-muted">
              <span className="inline-flex items-center gap-1.5">
                <span
                  aria-hidden="true"
                  className={cn(
                    "h-1 w-1 rounded-full",
                    pipeline === "fixed" ? "bg-moss" : "bg-amber",
                  )}
                />
                {pipeline} retrieval
              </span>
              <span>tenant · {tenant}</span>
              <span className="ml-auto hidden sm:inline">
                {API_MODE === "mock" ? "fixture mode" : "live API"}
              </span>
            </div>
          </form>

          {error ? (
            <div
              role="alert"
              className="rounded-2xl border border-danger/25 bg-danger-soft/60 px-4 py-3 text-sm text-danger"
            >
              <p className="font-medium">The query failed.</p>
              <p className="mt-0.5 text-xs leading-5">{error}</p>
            </div>
          ) : null}

          <div className="space-y-6" aria-live="polite">
            {turns.length === 0 && !isLoading ? (
              <section className="surface relative overflow-hidden p-6 sm:p-8">
                <div
                  aria-hidden="true"
                  className="pointer-events-none absolute -right-20 -top-24 h-64 w-64 rounded-full border border-ember/15"
                />
                <div
                  aria-hidden="true"
                  className="pointer-events-none absolute -right-8 -top-8 h-40 w-40 rounded-full border border-ember/20"
                />
                <p className="eyebrow">Evidence trail</p>
                <h2 className="mt-2 max-w-lg font-display text-3xl leading-[1.1] tracking-[-0.02em] text-ink sm:text-[2.15rem]">
                  Start with a question.
                  <br />
                  <span className="italic text-ember">End with a source.</span>
                </h2>
                <p className="mt-3 max-w-xl text-sm leading-6 text-muted">
                  Pick a sample prompt, or ask your own. The fixed pipeline returns claims with
                  page-level citations. Click any citation to inspect the exact document block.
                </p>

                <div className="mt-6 grid gap-2.5 sm:grid-cols-3">
                  {[
                    {
                      icon: FileSearch,
                      title: "Claim-level citations",
                      copy: "Every assertion carries a source block, not a vague page link.",
                    },
                    {
                      icon: GitCompare,
                      title: "Baseline vs fixed",
                      copy: "Switch pipelines after a run and see the same query through both.",
                    },
                    {
                      icon: ShieldCheck,
                      title: "Honest abstention",
                      copy: "If the evidence is missing, the fixed pipeline refuses to guess.",
                    },
                  ].map((feature) => {
                    const Icon = feature.icon;
                    return (
                      <div
                        key={feature.title}
                        className="rounded-2xl border border-line/80 bg-paper/45 p-3.5"
                      >
                        <Icon aria-hidden="true" className="h-4 w-4 text-ember" />
                        <p className="mt-2 text-xs font-semibold text-ink">{feature.title}</p>
                        <p className="mt-1 text-[0.68rem] leading-5 text-muted">{feature.copy}</p>
                      </div>
                    );
                  })}
                </div>

                <blockquote className="mt-6 border-l-2 border-ember/60 pl-4 font-display text-lg italic leading-7 text-ink-soft">
                  “The interesting part is not the answer. It is whether you can verify it.”
                </blockquote>
              </section>
            ) : null}

            {turns.map((turn) => (
              <div key={turn.id} className="animate-rise space-y-2.5">
                <div className="flex items-start gap-2.5 px-1">
                  <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-ink text-surface">
                    <ArrowUp aria-hidden="true" className="h-3 w-3" />
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium leading-6 text-ink">{turn.question}</p>
                    <p className="mt-0.5 font-mono text-[0.6rem] uppercase tracking-[0.12em] text-muted">
                      {turn.tenant} · {turn.pipeline} pipeline · trace{" "}
                      {formatTrace(turn.response.trace_id)}
                    </p>
                  </div>
                </div>
                <AnswerCard
                  response={turn.response}
                  tenant={turn.tenant}
                  pipeline={turn.pipeline}
                  onOpenCitation={(citation, citationTenant) =>
                    setActiveCitation({ citation, tenant: citationTenant })
                  }
                />
              </div>
            ))}

            {isLoading ? (
              <div className="surface overflow-hidden" role="status" aria-label="Running query">
                <div className="flex items-center gap-2 border-b border-line/70 px-5 py-3.5 sm:px-6">
                  <span className="flex items-center gap-1">
                    {[0, 1, 2].map((dot) => (
                      <span
                        key={dot}
                        className="h-1.5 w-1.5 animate-pulse rounded-full bg-ember"
                        style={{ animationDelay: `${dot * 140}ms` }}
                      />
                    ))}
                  </span>
                  <span className="text-[0.68rem] font-medium text-muted">
                    Running the {pipeline} pipeline across {tenant}…
                  </span>
                </div>
                <div className="space-y-3 px-5 py-6 sm:px-6">
                  <div className="skeleton h-4 w-3/4 rounded" />
                  <div className="skeleton h-4 w-full rounded" />
                  <div className="skeleton h-4 w-5/6 rounded" />
                  <div className="skeleton mt-5 h-24 w-full rounded-2xl" />
                </div>
              </div>
            ) : null}

            <div ref={endRef} />
          </div>
        </div>
      </div>

      <CitationDrawer
        citation={activeCitation?.citation ?? null}
        tenant={activeCitation?.tenant ?? tenant}
        onClose={closeDrawer}
      />
    </>
  );
}
