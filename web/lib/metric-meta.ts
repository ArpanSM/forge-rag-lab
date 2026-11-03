import type { EvalMetricRow } from "./types";

export type MetricUnit = "ratio" | "ms" | "count";

export type MetricGroup = "retrieval" | "answer" | "citations" | "reliability" | "latency";

export interface MetricMeta {
  label: string;
  description: string;
  group: MetricGroup;
  unit: MetricUnit;
  lowerIsBetter?: boolean;
}

export const METRIC_GROUPS: Array<{
  id: MetricGroup;
  label: string;
  description: string;
}> = [
  {
    id: "retrieval",
    label: "Retrieval",
    description: "Did the right blocks make it into context?",
  },
  {
    id: "answer",
    label: "Answer quality",
    description: "Correctness and faithfulness of the written answer.",
  },
  {
    id: "citations",
    label: "Citations",
    description: "Whether every reference lands on the right page and span.",
  },
  {
    id: "reliability",
    label: "Reliability",
    description: "Stale answers, version conflicts and abstention behaviour.",
  },
  {
    id: "latency",
    label: "Latency",
    description: "End-to-end response time. Lower is better.",
  },
];

const METRICS: Record<string, MetricMeta> = {
  recall_at_5: {
    label: "Recall @ 5",
    description: "Share of gold blocks present in the first five retrieved chunks.",
    group: "retrieval",
    unit: "ratio",
  },
  recall_at_10: {
    label: "Recall @ 10",
    description: "Share of gold blocks present in the first ten retrieved chunks.",
    group: "retrieval",
    unit: "ratio",
  },
  all_gold_at_10: {
    label: "All gold @ 10",
    description: "Questions where every gold block appears in the top ten.",
    group: "retrieval",
    unit: "ratio",
  },
  context_precision: {
    label: "Context precision",
    description: "Share of retrieved context that is actually relevant.",
    group: "retrieval",
    unit: "ratio",
  },
  context_recall: {
    label: "Context recall",
    description: "Share of the evidence needed for the answer that was retrieved.",
    group: "retrieval",
    unit: "ratio",
  },
  answer_correctness: {
    label: "Answer correctness",
    description: "Judge-scored agreement with the gold answer.",
    group: "answer",
    unit: "ratio",
  },
  factual_f1: {
    label: "Factual F1",
    description: "Token-level factual overlap with the reference answer.",
    group: "answer",
    unit: "ratio",
  },
  faithfulness: {
    label: "Faithfulness",
    description: "Share of answer claims supported by the retrieved context.",
    group: "answer",
    unit: "ratio",
  },
  citation_page_accuracy: {
    label: "Citation page accuracy",
    description: "Citations that point at the correct page.",
    group: "citations",
    unit: "ratio",
  },
  citation_span_hit: {
    label: "Citation span hit",
    description: "Citations whose quote overlaps the supporting block span.",
    group: "citations",
    unit: "ratio",
  },
  alce_precision: {
    label: "ALCE precision",
    description: "Correct citations divided by all citations in the answer.",
    group: "citations",
    unit: "ratio",
  },
  alce_recall: {
    label: "ALCE recall",
    description: "Gold sources that were cited at least once.",
    group: "citations",
    unit: "ratio",
  },
  alce_coverage: {
    label: "ALCE coverage",
    description: "Answer claims that carry at least one valid citation.",
    group: "citations",
    unit: "ratio",
  },
  stale_answer_rate: {
    label: "Stale answer rate",
    description: "Answers that repeat a superseded version. Lower is better.",
    group: "reliability",
    unit: "ratio",
    lowerIsBetter: true,
  },
  stale_citation_rate: {
    label: "Stale citation rate",
    description: "Citations that resolve to a superseded version. Lower is better.",
    group: "reliability",
    unit: "ratio",
    lowerIsBetter: true,
  },
  disambiguation_accuracy: {
    label: "Version disambiguation",
    description: "Correct version chosen when the corpus contains conflicting pages.",
    group: "reliability",
    unit: "ratio",
  },
  abstention_accuracy: {
    label: "Abstention accuracy",
    description: "Correct abstentions plus answerable questions that were answered.",
    group: "reliability",
    unit: "ratio",
  },
  false_abstention_rate: {
    label: "False abstention rate",
    description: "Answerable questions where the system refused to answer. Lower is better.",
    group: "reliability",
    unit: "ratio",
    lowerIsBetter: true,
  },
  selective_accuracy: {
    label: "Selective accuracy",
    description: "Accuracy on the questions the system chose to answer.",
    group: "reliability",
    unit: "ratio",
  },
  p50_latency_ms: {
    label: "p50 latency",
    description: "Median end-to-end response time.",
    group: "latency",
    unit: "ms",
    lowerIsBetter: true,
  },
  p95_latency_ms: {
    label: "p95 latency",
    description: "95th percentile end-to-end response time.",
    group: "latency",
    unit: "ms",
    lowerIsBetter: true,
  },
};

export function metricMeta(metric: string): MetricMeta {
  return (
    METRICS[metric] ?? {
      label: metric
        .replace(/_/g, " ")
        .replace(/\b\w/g, (letter) => letter.toUpperCase()),
      description: "Evaluation metric.",
      group: "reliability",
      unit: metric.includes("latency") ? "ms" : "ratio",
    }
  );
}

export function formatMetric(value: number, unit: MetricUnit): string {
  if (unit === "ms") {
    return new Intl.NumberFormat("en", { maximumFractionDigits: 0 }).format(value) + " ms";
  }
  if (unit === "count") {
    return new Intl.NumberFormat("en", { maximumFractionDigits: 0 }).format(value);
  }
  const percent = value * 100;
  return `${percent.toFixed(percent < 10 && percent % 1 !== 0 ? 1 : 0)}%`;
}

export function formatDelta(row: EvalMetricRow, unit: MetricUnit): string {
  if (unit === "ms") {
    const sign = row.delta > 0 ? "+" : row.delta < 0 ? "−" : "±";
    return `${sign}${new Intl.NumberFormat("en", { maximumFractionDigits: 0 }).format(
      Math.abs(row.delta),
    )} ms`;
  }
  const points = row.delta * 100;
  const sign = points > 0 ? "+" : points < 0 ? "−" : "±";
  return `${sign}${Math.abs(points).toFixed(Math.abs(points) < 10 && Math.abs(points) % 1 !== 0 ? 1 : 0)} pts`;
}

export function deltaTone(row: EvalMetricRow, meta: MetricMeta): "good" | "bad" | "flat" {
  if (Math.abs(row.delta) < 0.0001) return "flat";
  const improved = meta.lowerIsBetter ? row.delta < 0 : row.delta > 0;
  return improved ? "good" : "bad";
}

export function metricBarWidth(value: number, unit: MetricUnit): number {
  if (unit === "ms") {
    return Math.max(2, Math.min(100, (value / 3000) * 100));
  }
  return Math.max(2, Math.min(100, value * 100));
}
