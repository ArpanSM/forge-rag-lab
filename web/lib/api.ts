import {
  MOCK_DEMO_QUESTIONS,
  MOCK_EVAL_SUMMARY,
  MOCK_FAILURES,
  mockDocBlock,
  mockQuery,
} from "./mock";
import { API_BASE_URL, API_MODE } from "./runtime";
import type {
  DemoQuestion,
  DocBlock,
  EvalSummary,
  FailureCase,
  QueryRequest,
  QueryResponse,
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
  return get<EvalSummary>("/api/eval/summary", signal);
}

export async function fetchFailures(signal?: AbortSignal): Promise<FailureCase[]> {
  if (API_MODE === "mock") {
    await wait(320, signal);
    return MOCK_FAILURES;
  }
  return get<FailureCase[]>("/api/eval/failures", signal);
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
