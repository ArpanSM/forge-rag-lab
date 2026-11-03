export type TenantId = "northwind" | "acme";

export type Pipeline = "baseline" | "fixed";

export type QuestionCategory =
  | "single_hop"
  | "multi_hop"
  | "version_specific"
  | "conflicting"
  | "unanswerable";

export interface Citation {
  doc_id: string;
  title: string;
  version: string;
  page: number;
  block_id: string;
  anchor: string;
  quote: string;
}

export interface Claim {
  claim_id: string;
  text: string;
  citations: Citation[];
}

export interface QueryRequest {
  tenant_id: TenantId;
  question: string;
  pipeline: Pipeline;
}

export interface QueryResponse {
  answer: string;
  abstained: boolean;
  claims: Claim[];
  latency_ms: number;
  model: string;
  pipeline: Pipeline;
  trace_id: string;
}

export interface DemoQuestion {
  id: string;
  tenant_id: TenantId;
  question: string;
  category: QuestionCategory;
  label?: string;
}

export interface EvalMetricRow {
  metric: string;
  baseline: number;
  fixed: number;
  delta: number;
  n: number;
}

export interface EvalSummary {
  generated_at: string;
  rows: EvalMetricRow[];
  note?: string;
}

export interface FailureCase {
  question_id: string;
  category: QuestionCategory;
  question: string;
  baseline_answer: string;
  fixed_answer: string;
  failure: string;
  fixed_citations: Citation[];
  baseline_citations?: Citation[];
  explanation?: string;
}

export interface DocBlock {
  doc_id: string;
  tenant_id: TenantId;
  title: string;
  version: string;
  page: number;
  block_id: string;
  anchor: string;
  heading: string;
  text: string;
}

export interface ApiHealth {
  status: string;
  version: string;
  qdrant: string;
  model_provider: string;
}
