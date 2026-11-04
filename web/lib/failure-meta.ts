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
      "A long page is truncated before the answer is generated. Structure-aware chunks retain the overage detail and reranking promotes the block that contains it.",
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
    label: "Cross-tenant isolation check",
    explanation:
      "Tenant isolation is enforced on every retrieval and citation read. This check verifies that a private page from one tenant never enters another tenant's evidence set.",
    severity: "high",
  },
  stale_answer: {
    label: "Stale answer",
    explanation:
      "The answer repeats a superseded version instead of the current one. The fixed pipeline filters by version before retrieval and reranking.",
    severity: "high",
  },
  false_abstention: {
    label: "False abstention",
    explanation:
      "The system refused an answerable question. The fixed pipeline only abstains when the evidence threshold is not met.",
    severity: "medium",
  },
  missed_abstention: {
    label: "Missed abstention",
    explanation:
      "The system answered a question the corpus cannot support. The fixed pipeline checks answerability before generation.",
    severity: "high",
  },
  no_disambiguation: {
    label: "No disambiguation",
    explanation:
      "The system blended two versions instead of choosing the current one. Version filters and conflict checks keep the versions separate.",
    severity: "high",
  },
  citation_page_miss: {
    label: "Citation page miss",
    explanation:
      "A citation points at the wrong page. Block-level metadata keeps page and anchor aligned with the evidence.",
    severity: "medium",
  },
  retrieval_miss: {
    label: "Retrieval miss",
    explanation:
      "At least one gold block was missing from the retrieved context. Hybrid retrieval and reranking lift recall at the top of the list.",
    severity: "medium",
  },
  all_gold_miss: {
    label: "All-gold miss",
    explanation:
      "None of the gold blocks reached the top ten. The fixed pipeline combines dense and sparse retrieval before reranking.",
    severity: "high",
  },
  pipeline_error: {
    label: "Pipeline error",
    explanation:
      "The pipeline failed before producing an answer. The failure is kept in the report instead of being hidden by an average.",
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
  prompt_injection: "Prompt injection",
};

export function categoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? humanize(category);
}
