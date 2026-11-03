import {
  MOCK_DEMO_QUESTIONS,
  MOCK_EVAL_SUMMARY,
  MOCK_FAILURES,
  mockDocBlock,
  mockQuery,
} from "./mock";
import { API_BASE_URL, API_MODE } from "./runtime";
import type {
  Citation,
  DemoQuestion,
  DocBlock,
  EvalMetricRow,
  EvalSummary,
  FailureCase,
  QueryRequest,
  QueryResponse,
  QuestionCategory,
  TenantId,
} from "./types";

export { API_BASE_URL, API_MODE } from "./runtime";

const baseUrl = API_BASE_URL;

export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function wait(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException("Aborted", "AbortError"));
      return;
    }
    const timeout = window.setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        window.clearTimeout(timeout);
        reject(new DOMException("Aborted", "AbortError"));
      },
      { once: true },
    );
  });
}

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    headers: { Accept: "application/json" },
    signal,
  });
  if (!response.ok) {
    throw new ApiError(`The API returned ${response.status} for ${path}.`, response.status);
  }
  return (await response.json()) as T;
}

async function post<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    throw new ApiError(`The API returned ${response.status} for ${path}.`, response.status);
  }
  return (await response.json()) as T;
}

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asText(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function asNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function asCitation(value: unknown): Citation | undefined {
  if (!isRecord(value)) return undefined;
  const docId = asText(value.doc_id);
  if (!docId) return undefined;
  return {
    doc_id: docId,
    title: asText(value.title) ?? docId,
    version: asText(value.version) ?? "unknown",
    page: asNumber(value.page) ?? 1,
    block_id: asText(value.block_id) ?? "unknown",
    anchor: asText(value.anchor) ?? "",
    quote: asText(value.quote) ?? "",
  };
}

function citationList(value: unknown): Citation[] {
  return Array.isArray(value)
    ? value.map(asCitation).filter((citation): citation is Citation => Boolean(citation))
    : [];
}

function pairedRows(rows: unknown[]): EvalMetricRow[] {
  return rows.flatMap((row) => {
    if (!isRecord(row)) return [];
    const metric = asText(row.metric);
    const baseline = asNumber(row.baseline);
    const fixed = asNumber(row.fixed);
    if (!metric || baseline === undefined || fixed === undefined) {
      return [];
    }
    const delta = asNumber(row.delta) ?? Math.round((fixed - baseline) * 1e6) / 1e6;
    return [
      {
        metric,
        baseline,
        fixed,
        delta,
        n: asNumber(row.n) ?? 0,
      },
    ];
  });
}

function pivotReportRows(rows: unknown[]): EvalMetricRow[] {
  const records = rows.filter(isRecord);
  const overall = records.filter((row) => asText(row.category) === "overall");
  const source =
    overall.length > 0
      ? overall
      : records.filter((row) => asText(row.category) === undefined || asText(row.category) === "");
  if (source.length === 0) return [];

  const grouped = new Map<string, { baseline?: number; fixed?: number; n: number }>();
  for (const row of source) {
    const metric = asText(row.metric);
    const pipeline = asText(row.pipeline);
    const value = asNumber(row.value);
    if (!metric || value === undefined) continue;
    if (pipeline !== "baseline" && pipeline !== "fixed") continue;
    const entry = grouped.get(metric) ?? { n: 0 };
    entry[pipeline] = value;
    entry.n = Math.max(entry.n, asNumber(row.n) ?? 0);
    grouped.set(metric, entry);
  }

  return [...grouped.entries()].flatMap(([metric, entry]) => {
    if (entry.baseline === undefined || entry.fixed === undefined) return [];
    return [
      {
        metric,
        baseline: entry.baseline,
        fixed: entry.fixed,
        delta: Math.round((entry.fixed - entry.baseline) * 1e6) / 1e6,
        n: entry.n,
      },
    ];
  });
}

function normaliseSummary(payload: unknown): EvalSummary {
  if (!isRecord(payload)) {
    return { generated_at: null, rows: [] };
  }
  const rows = Array.isArray(payload.rows) ? payload.rows : [];
  const paired = pairedRows(rows);
  return {
    generated_at: asText(payload.generated_at) ?? null,
    rows: paired.length === rows.length && rows.length > 0 ? paired : pivotReportRows(rows),
    note: asText(payload.note),
  };
}

function normaliseFailures(payload: unknown): FailureCase[] {
  const rows = Array.isArray(payload) ? payload : [];
  const paired: FailureCase[] = [];
  const grouped = new Map<string, FailureCase>();

  rows.forEach((raw, index) => {
    if (!isRecord(raw)) return;
    const questionId = asText(raw.question_id) ?? `failure-${index}`;
    const category = (asText(raw.category) ?? "single_hop") as QuestionCategory;
    const question = asText(raw.question) ?? "";
    const failure = asText(raw.failure) ?? "pipeline_error";
    const baselineAnswer = asText(raw.baseline_answer);
    const fixedAnswer = asText(raw.fixed_answer);

    if (baselineAnswer !== undefined || fixedAnswer !== undefined) {
      paired.push({
        question_id: questionId,
        category,
        question,
        baseline_answer: baselineAnswer ?? "",
        fixed_answer: fixedAnswer ?? "",
        failure,
        fixed_citations: citationList(raw.fixed_citations),
        baseline_citations: citationList(raw.baseline_citations),
        explanation: asText(raw.explanation),
      });
      return;
    }

    const existing = grouped.get(questionId) ?? {
      question_id: questionId,
      category,
      question,
      baseline_answer: "",
      fixed_answer: "",
      failure,
      fixed_citations: [],
      baseline_citations: [],
    };
    const pipeline = asText(raw.pipeline);
    const answer = asText(raw.answer) ?? "";
    const citations = citationList(raw.citations);
    if (pipeline === "baseline") {
      existing.baseline_answer = answer;
      existing.baseline_citations = citations;
    } else {
      existing.fixed_answer = answer;
      existing.fixed_citations = citations;
      existing.failure = failure;
    }
    if (question) existing.question = question;
    const reasons = Array.isArray(raw.reasons)
      ? raw.reasons.filter((reason): reason is string => typeof reason === "string")
      : [];
    if (reasons.length > 0) existing.explanation = reasons.join(" · ");
    grouped.set(questionId, existing);
  });

  return [...paired, ...grouped.values()];
}

export async function fetchDemoQuestions(signal?: AbortSignal): Promise<DemoQuestion[]> {
  if (API_MODE === "mock") {
    await wait(120, signal);
    return MOCK_DEMO_QUESTIONS;
  }
  return get<DemoQuestion[]>("/api/demo/questions", signal);
}

export async function askQuestion(
  request: QueryRequest,
  signal?: AbortSignal,
): Promise<QueryResponse> {
  if (API_MODE === "mock") {
    await wait(request.pipeline === "fixed" ? 880 : 540, signal);
    return mockQuery(request);
  }
  return post<QueryResponse>("/api/query", request, signal);
}

export async function fetchEvalSummary(signal?: AbortSignal): Promise<EvalSummary> {
  if (API_MODE === "mock") {
    await wait(260, signal);
    return MOCK_EVAL_SUMMARY;
  }
  return normaliseSummary(await get<unknown>("/api/eval/summary", signal));
}

export async function fetchFailures(signal?: AbortSignal): Promise<FailureCase[]> {
  if (API_MODE === "mock") {
    await wait(320, signal);
    return MOCK_FAILURES;
  }
  return normaliseFailures(await get<unknown>("/api/eval/failures", signal));
}

export async function fetchDocBlock(
  tenantId: TenantId,
  docId: string,
  blockId: string,
  version?: string,
  signal?: AbortSignal,
): Promise<DocBlock> {
  if (API_MODE === "mock") {
    await wait(240, signal);
    const block = mockDocBlock(tenantId, docId, blockId, version);
    if (!block) {
      throw new ApiError("That block is not part of the bundled fixtures.", 404);
    }
    return block;
  }
  const versionParam = version ? `&version=${encodeURIComponent(version)}` : "";
  const path = `/api/docs/${encodeURIComponent(docId)}/blocks/${encodeURIComponent(
    blockId,
  )}?tenant_id=${encodeURIComponent(tenantId)}${versionParam}`;
  return get<DocBlock>(path, signal);
}

export function errorMessage(error: unknown): string {
  if (error instanceof DOMException && error.name === "AbortError") {
    return "Request cancelled.";
  }
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong while contacting the API.";
}
