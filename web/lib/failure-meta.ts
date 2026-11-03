import { humanize } from "./utils";

export interface FailureMeta {
  label: string;
  explanation: string;
  severity: "high" | "medium" | "low";
}

const FAILURES: Record<string, FailureMeta> = {
  stale_citation: {
    label: "Stale citation",
    explanation:
      "Dense-only retrieval ranks a superseded v1 page above v3. The fixed pipeline filters by version before reranking, so the citation resolves to the current block.",
    severity: "high",
  },
  wrong_page: {
    label: "Wrong page",
    explanation:
      "The retrieved text is relevant but its page metadata is wrong. Structure-aware chunking keeps page and block boundaries intact, so the drawer lands on the exact source.",
    severity: "medium",
  },
  missed_detail: {
    label: "Missed detail",
    explanation:
      "A long page is truncated before the answer is generated. Structure-aware chunks retain the refund detail and reranking promotes the block that contains it.",
    severity: "medium",
  },
  no_abstention: {
    label: "No abstention",
    explanation:
      "The baseline always answers. The fixed pipeline checks answerability first and abstains when no retrieved block supports the question.",
    severity: "high",
  },
  prompt_injection: {
    label: "Prompt injection",
    explanation:
      "Document text is treated as untrusted data, not instructions. The injection sentence is stripped from the context and never reaches the generator as a directive.",
    severity: "high",
  },
  conflicting_versions: {
    label: "Conflicting versions",
    explanation:
      "Two versions disagree about SSO availability. Fixed retrieval prefers the current version, then reports the conflict instead of blending the two claims.",
    severity: "high",
  },
  cross_tenant_leak: {
    label: "Cross-tenant leak",
    explanation:
      "The baseline ignores the tenant filter and retrieves another tenant's private runbook. The fixed pipeline scopes every retrieval and citation read to the selected tenant.",
    severity: "high",
  },
};

export function failureMeta(code: string): FailureMeta {
  return (
    FAILURES[code] ?? {
      label: humanize(code),
      explanation: "Evaluation fixture for this failure mode.",
      severity: "medium",
    }
  );
}

export const CATEGORY_LABELS: Record<string, string> = {
  single_hop: "Single hop",
  multi_hop: "Multi hop",
  version_specific: "Version specific",
  conflicting: "Conflicting",
  unanswerable: "Unanswerable",
};

export function categoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? humanize(category);
}
